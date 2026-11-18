export function makeTempDir(): string;
export function writeFixture(root: string, relative: string, content: string | Uint8Array): void;
export function removeDir(dir: string): void;
export function randomContent(bytes: number): Uint8Array;
