import { generateText, generateObject } from 'ai';
import { createOpenAI } from '@ai-sdk/openai';
import { NextResponse } from 'next/server';
import { z } from 'zod';

// Vercel AI Gateway / OpenAI-compatible Gateway client configuration
const apiKey = process.env.AI_GATEWAY_API_KEY || '';

const gatewayOpenAI = createOpenAI({
  apiKey: apiKey,
  baseURL: 'https://ai-gateway.vercel.sh/v1',
  headers: {
    'x-api-key': apiKey,
  },
});

export async function POST(req: Request) {
  try {
    const { task, prompt, image, messages } = await req.json();

    if (!apiKey) {
      return NextResponse.json(
        { error: 'AI_GATEWAY_API_KEY is not configured in .env.local' },
        { status: 400 }
      );
    }

    // MULTI-MODEL ROUTING BASED ON TASK TYPE
    switch (task) {
      case 'intent': {
        // Fast LLM Reasoning for intent & entity extraction
        const model = gatewayOpenAI('google/gemini-1.5-flash');
        const { object } = await generateObject({
          model,
          schema: z.object({
            intent: z.string(),
            entities: z.object({
              commodity: z.string().nullable(),
              quantity: z.number().nullable(),
              unit: z.string().nullable(),
              price: z.number().nullable(),
              location: z.string().nullable(),
            }),
            confidence: z.number(),
            response_hint: z.string(),
          }),
          prompt: prompt || 'Analyze user intent for agricultural trading.',
        });

        return NextResponse.json({ success: true, task: 'intent', result: object });
      }

      case 'vision': {
        // Multimodal AI Vision model for agricultural crop photo grading
        const visionModel = gatewayOpenAI('google/gemini-1.5-flash');
        const content: any[] = [
          {
            type: 'text',
            text: 'Analyze this agricultural produce image (e.g. Shea Butter, Maize, Sorghum, Peanuts). Grade quality (A, B, or C), evaluate color, texture, impurities, estimate market grade, and give visual evidence rationale.',
          },
        ];

        if (image) {
          content.push({
            type: 'image',
            image: image,
          });
        }

        const { text } = await generateText({
          model: visionModel,
          messages: [{ role: 'user', content }],
        });

        return NextResponse.json({ success: true, task: 'vision', result: text });
      }

      case 'negotiation': {
        // High-reasoning model for contract/bidding negotiations
        const reasoningModel = gatewayOpenAI('openai/gpt-4o-mini');
        const { text } = await generateText({
          model: reasoningModel,
          messages: messages || [{ role: 'user', content: prompt }],
        });

        return NextResponse.json({ success: true, task: 'negotiation', result: text });
      }

      default: {
        // Default general AI response
        const defaultModel = gatewayOpenAI('google/gemini-1.5-flash');
        const { text } = await generateText({
          model: defaultModel,
          prompt: prompt || 'Hello from ZAA Multi-Model Assistant',
        });

        return NextResponse.json({ success: true, task: 'general', result: text });
      }
    }
  } catch (error: any) {
    console.error('Vercel AI Gateway Route Error:', error);
    return NextResponse.json(
      { error: error.message || 'AI Gateway execution failed' },
      { status: 500 }
    );
  }
}
