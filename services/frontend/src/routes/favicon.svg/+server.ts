import type { RequestHandler } from '@sveltejs/kit';
import { readFile } from 'node:fs/promises';

export const GET: RequestHandler = async () => {
  try {
    const data = await readFile('static/favicon.svg');
    return new Response(data, {
      status: 200,
      headers: {
        'content-type': 'image/svg+xml'
      }
    });
  } catch (e) {
    return new Response('Not found', { status: 404 });
  }
};
