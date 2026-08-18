"""Limite de tentativas por IP nas rotas de autenticação.

O identificador é o IP real do visitante, não o do proxy: em produção o
tráfego chega por cloudflared e nginx, que acrescentam CF-Connecting-IP e
X-Forwarded-For. Sem isso todos os usuários dividiriam o mesmo balde e o
primeiro a errar a senha travaria os demais.
"""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def client_ip(request: Request) -> str:
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=client_ip)
