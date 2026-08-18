#!/usr/bin/env node

import path from 'node:path';
import fs from 'node:fs';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const ESC = '\x1b';
const CLEAR_LINE = `${ESC}[2K`;
const HIDE_CURSOR = `${ESC}[?25l`;
const SHOW_CURSOR = `${ESC}[?25h`;

function select(title, items) {
    return new Promise((resolve, reject) => {
        let idx = 0;
        const out = process.stdout;

        function render(first) {
            if (!first) out.write(`${ESC}[${items.length + 1}A`);
            out.write(`${CLEAR_LINE}${title}\n`);
            for (let i = 0; i < items.length; i++) {
                const selected = i === idx;
                const pointer = selected ? `${ESC}[36m>` : ' ';
                const text = selected ? `${ESC}[36m${items[i].label}${ESC}[0m` : items[i].label;
                out.write(`${CLEAR_LINE}${pointer} ${text}${ESC}[0m\n`);
            }
        }

        function cleanup() {
            process.stdin.setRawMode(false);
            process.stdin.pause();
            process.stdin.removeListener('data', onData);
            out.write(SHOW_CURSOR);
        }

        function onData(buffer) {
            const key = buffer.toString();
            if (key === '\x03') {
                cleanup();
                reject(new Error('cancelled'));
            } else if (key === `${ESC}[A` || key === 'k') {
                idx = (idx - 1 + items.length) % items.length;
                render(false);
            } else if (key === `${ESC}[B` || key === 'j') {
                idx = (idx + 1) % items.length;
                render(false);
            } else if (key === '\r' || key === '\n') {
                cleanup();
                resolve(items[idx].value);
            }
        }

        out.write(HIDE_CURSOR);
        process.stdin.setRawMode(true);
        process.stdin.resume();
        process.stdin.on('data', onData);
        render(true);
    });
}

function prompt(question) {
    return new Promise((resolve) => {
        process.stdout.write(question);
        process.stdin.setRawMode(false);
        process.stdin.resume();
        process.stdin.setEncoding('utf8');
        let line = '';
        function onData(chunk) {
            line += chunk;
            const newline = line.search(/[\r\n]/);
            if (newline !== -1) {
                process.stdin.removeListener('data', onData);
                process.stdin.pause();
                resolve(line.slice(0, newline).trim());
            }
        }
        process.stdin.on('data', onData);
    });
}

function findMedia(dir) {
    const skipped = new Set(['node_modules', '.git', 'dist', 'pieces']);
    const supportedExtensions = new Set(['.mp4', '.webm']);
    const found = [];
    function walk(current) {
        let entries;
        try {
            entries = fs.readdirSync(current, { withFileTypes: true });
        } catch {
            return;
        }
        for (const entry of entries) {
            const location = path.join(current, entry.name);
            if (entry.isDirectory() && !skipped.has(entry.name)) walk(location);
            else if (entry.isFile() && supportedExtensions.has(path.extname(entry.name).toLowerCase())) found.push(location);
        }
    }
    walk(dir);
    return found;
}

function valueOr(answer, fallback) {
    return answer === '' ? fallback : answer;
}

async function chooseMedia() {
    const mediaFiles = findMedia(here);
    if (mediaFiles.length === 0) {
        throw new Error('No MP4 or WebM files found. please put one in this project folder or subfolder and try again');
    }
    const items = mediaFiles.map((mediaFile) => ({
        label: path.relative(here, mediaFile),
        value: mediaFile,
    }));
    return select('choose a video below', items);
}

async function chooseSize() {
    const selected = await select('Choose the screen resolution', [
        { label: '80 x 45', value: '80x45' },
        { label: '64 x 36', value: '64x36' },
        { label: '48 x 27', value: '48x27' },
        { label: '32 x 18', value: '32x18' },
        { label: 'Custom', value: null },
    ]);
    return selected ?? await prompt('Resolution (widthxheight): ');
}

async function main() {
    const video = await chooseMedia();
    const mode = await select('choose a color mode', [
        { label: 'Full color', value: 'color' },
        { label: 'block + empty space', value: 'mono' },
    ]);
    const size = await chooseSize();

    console.log('\nStarting coords (top left corner');
    const x = valueOr(await prompt('X [0]: '), '0');
    const y = valueOr(await prompt('Y [64]: '), '64');
    const z = valueOr(await prompt('Z [0]: '), '0');

    const args = [
        path.join(here, 'generate.py'), video,
        '--output', path.join(here, 'output'),
        '--mode', mode, '--size', size, '--origin', x, y, z, '--plane', 'xz',
    ];

    if (mode === 'mono') {
        args.push(
            '--foreground', valueOr(await prompt('Block [white_concrete]: '), 'white_concrete'),
            '--background', valueOr(await prompt('Background block [air]: '), 'air'),
        );
    }

    args.push('--overwrite');
    console.log('');
    const child = spawn(process.env.PYTHON || 'python3', args, { stdio: 'inherit' });
    child.on('error', (error) => {
        console.error(error.message);
        process.exitCode = 1;
    });
    child.on('exit', (code) => {
        process.exitCode = code ?? 1;
    });
}

main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
});