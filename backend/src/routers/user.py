import logging
import secrets
import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlalchemy.future import select

from src import models, schemas, auth
from src.config import settings
from src.database import get_db
from src.ratelimit import limiter
from src.email_service import send_password_reset_email

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


async def _resgatar_convite(db: AsyncSession, codigo: str | None) -> models.InviteCode | None:
    """Devolve o convite a marcar como usado, ou None na primeira conta do servidor.

    Levanta 403 quando o codigo falta, nao existe, ja foi usado ou venceu — a
    mesma mensagem nos quatro casos, para nao virar oraculo de codigo valido.
    """
    total_usuarios = await db.scalar(select(func.count()).select_from(models.User))
    if not total_usuarios:
        return None  # primeira conta: e assim que o dono entra

    recusa = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Código de convite inválido ou já utilizado.",
    )
    if not codigo or not codigo.strip():
        raise recusa

    result = await db.execute(
        select(models.InviteCode).filter(models.InviteCode.code == codigo.strip())
    )
    convite = result.scalars().first()
    if convite is None or convite.used_at is not None:
        raise recusa
    if convite.expires_at is not None and convite.expires_at < datetime.utcnow():
        raise recusa
    return convite


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def register(request: Request, user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    convite = await _resgatar_convite(db, user.invite_code)

    result = await db.execute(select(models.User).filter(models.User.email == user.email))
    db_user = result.scalars().first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    # flush em vez de commit: pega o id do usuario e marca o convite na mesma
    # transacao, para nao existir conta criada com convite ainda disponivel
    await db.flush()
    if convite is not None:
        convite.used_by_id = new_user.id
        convite.used_at = datetime.utcnow()
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/invites", response_model=schemas.InviteCodeResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/hour")
async def criar_convite(
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario_atual: models.User = Depends(auth.get_current_user),
):
    """Gera um convite de uso único, válido por 7 dias."""
    convite = models.InviteCode(
        code=secrets.token_urlsafe(9),
        created_by_id=usuario_atual.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(convite)
    await db.commit()
    await db.refresh(convite)
    return convite


@router.get("/invites", response_model=List[schemas.InviteCodeResponse])
async def listar_convites(
    db: AsyncSession = Depends(get_db),
    usuario_atual: models.User = Depends(auth.get_current_user),
):
    """Convites que este usuário gerou, do mais recente para o mais antigo."""
    result = await db.execute(
        select(models.InviteCode)
        .filter(models.InviteCode.created_by_id == usuario_atual.id)
        .order_by(models.InviteCode.created_at.desc())
    )
    return result.scalars().all()


@router.post("/login", response_model=schemas.Token)
@limiter.limit("5/minute;30/hour")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).filter(models.User.email == form_data.username))
    user = result.scalars().first()

    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
@limiter.limit("3/hour")
async def forgot_password(
    request: Request,
    body: schemas.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Request a password reset link. Always returns 200 to avoid user enumeration."""
    result = await db.execute(select(models.User).filter(models.User.email == body.email))
    user = result.scalars().first()

    if user:
        # Invalidate any existing unused tokens for this user
        existing = await db.execute(
            select(models.PasswordResetToken).filter(
                models.PasswordResetToken.user_id == user.id,
                models.PasswordResetToken.used == False,
            )
        )
        for old_token in existing.scalars().all():
            old_token.used = True

        token = str(uuid.uuid4())
        reset_token = models.PasswordResetToken(
            token=token,
            user_id=user.id,
            expires_at=datetime.utcnow() + timedelta(minutes=30),
        )
        db.add(reset_token)
        await db.commit()

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        background_tasks.add_task(_send_reset_email, user.email, reset_url)

    return {"message": "Se o e-mail existir, você receberá o link em breve."}


def _send_reset_email(to_email: str, reset_url: str) -> None:
    try:
        send_password_reset_email(to_email, reset_url)
    except Exception as e:
        logger.error(f"Failed to send password reset email to {to_email}: {e}")


@router.post("/reset-password", status_code=status.HTTP_200_OK)
@limiter.limit("10/hour")
async def reset_password(request: Request, body: schemas.ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Validate token and update password."""
    result = await db.execute(
        select(models.PasswordResetToken).filter(models.PasswordResetToken.token == body.token)
    )
    reset_token = result.scalars().first()

    if not reset_token or reset_token.used or reset_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link de recuperação inválido ou expirado.",
        )

    if len(body.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A senha precisa ter pelo menos 8 caracteres.",
        )

    user_result = await db.execute(select(models.User).filter(models.User.id == reset_token.user_id))
    user = user_result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    user.hashed_password = auth.get_password_hash(body.new_password)
    reset_token.used = True
    await db.commit()

    return {"message": "Senha redefinida com sucesso."}
