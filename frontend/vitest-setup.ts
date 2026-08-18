import '@testing-library/jest-dom';
// jsdom não implementa IndexedDB, e o Dexie ($lib/db) é carregado por quase
// todo módulo testado — sem este polyfill os testes morrem em MissingAPIError.
import 'fake-indexeddb/auto';
