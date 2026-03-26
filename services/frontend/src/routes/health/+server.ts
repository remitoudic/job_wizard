
import { json } from '@sveltejs/kit';

export function GET() {
    return json(
        { status: 'ok', timestamp: new Date().toISOString() },
        {
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
            }
        }
    );
}
