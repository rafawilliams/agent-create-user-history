import { configureAxe } from 'vitest-axe';

// jsdom no calcula diseño ni dibuja: el contraste (NFR6.2) se revisa a mano en Build and Test.
export const axe = configureAxe({ rules: { 'color-contrast': { enabled: false } } });
