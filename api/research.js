export const config = { runtime: 'edge' };

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

export default async function handler(req) {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: CORS });
  }
  if (req.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405, headers: { ...CORS, 'Content-Type': 'application/json' }
    });
  }

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return new Response(JSON.stringify({ error: 'API key not configured' }), {
      status: 500, headers: { ...CORS, 'Content-Type': 'application/json' }
    });
  }

  let body;
  try {
    body = await req.json();
  } catch {
    return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
      status: 400, headers: { ...CORS, 'Content-Type': 'application/json' }
    });
  }

  const { action, query, existingName, existingData } = body;

  let systemPrompt = `You are a helpful travel assistant for a Japan trip in May 2026.
You provide concise, accurate information about activities, restaurants, and attractions in Japan.
Always respond with valid JSON only — no markdown, no explanation outside the JSON.`;

  let userPrompt;

  if (action === 'enrich') {
    userPrompt = `Enrich this existing entry for a Japan trip itinerary app.
Existing name: ${existingName}
Existing data: ${JSON.stringify(existingData, null, 2)}

Return a JSON object with these fields (keep any existing good data, add/improve the rest):
{
  "name": "display name",
  "category": "one of: Cultural, Food, Nature, Shopping, Entertainment, Transport",
  "city": "one of: Tokyo, Hakone, Kyoto, Osaka",
  "tags": ["array", "of", "relevant", "tags"],
  "overview": "2-3 sentence description",
  "highlights": ["key highlight 1", "key highlight 2", "key highlight 3"],
  "tips": ["practical tip 1", "practical tip 2"],
  "hours": "opening hours string or null",
  "price": "price info string or null",
  "address": "Japanese address or area description",
  "website": null,
  "mapQuery": "Google Maps search string"
}`;
  } else if (action === 'new') {
    userPrompt = `Research this Japan travel topic for a May 2026 trip itinerary app: "${query}"

Return a JSON object:
{
  "name": "display name",
  "category": "one of: Cultural, Food, Nature, Shopping, Entertainment, Transport",
  "city": "one of: Tokyo, Hakone, Kyoto, Osaka",
  "tags": ["array", "of", "relevant", "tags"],
  "overview": "2-3 sentence description",
  "highlights": ["key highlight 1", "key highlight 2", "key highlight 3"],
  "tips": ["practical tip 1", "practical tip 2"],
  "hours": "opening hours string or null",
  "price": "price info string or null",
  "address": "Japanese address or area description",
  "website": null,
  "mapQuery": "Google Maps search string"
}`;
  } else if (action === 'event') {
    userPrompt = `Research this itinerary event for a Japan trip: "${query}"

Determine if this is an activity, food experience, or logistical note and return the most appropriate JSON.
Return a JSON object:
{
  "name": "display name",
  "type": "one of: activity, food, note",
  "category": "one of: Cultural, Food, Nature, Shopping, Entertainment, Transport",
  "city": "one of: Tokyo, Hakone, Kyoto, Osaka",
  "tags": ["relevant", "tags"],
  "overview": "2-3 sentence description",
  "highlights": ["key highlight 1", "key highlight 2"],
  "tips": ["practical tip 1"],
  "hours": "opening hours or null",
  "price": "price info or null",
  "address": "address or area",
  "website": null,
  "mapQuery": "Google Maps search string"
}`;
  } else {
    return new Response(JSON.stringify({ error: 'Invalid action' }), {
      status: 400, headers: { ...CORS, 'Content-Type': 'application/json' }
    });
  }

  try {
    const aiRes = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 1024,
        system: systemPrompt,
        messages: [{ role: 'user', content: userPrompt }],
      }),
    });

    if (!aiRes.ok) {
      const errText = await aiRes.text();
      return new Response(JSON.stringify({ error: 'AI API error', detail: errText }), {
        status: 502, headers: { ...CORS, 'Content-Type': 'application/json' }
      });
    }

    const aiData = await aiRes.json();
    const text = aiData.content?.[0]?.text || '';

    let parsed;
    try {
      parsed = JSON.parse(text);
    } catch {
      const match = text.match(/\{[\s\S]*\}/);
      if (match) {
        parsed = JSON.parse(match[0]);
      } else {
        return new Response(JSON.stringify({ error: 'Could not parse AI response', raw: text }), {
          status: 502, headers: { ...CORS, 'Content-Type': 'application/json' }
        });
      }
    }

    return new Response(JSON.stringify({ result: parsed }), {
      status: 200, headers: { ...CORS, 'Content-Type': 'application/json' }
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500, headers: { ...CORS, 'Content-Type': 'application/json' }
    });
  }
}
