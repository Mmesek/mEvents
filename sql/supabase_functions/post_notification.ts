import 'jsr:@supabase/functions-js/edge-runtime.d.ts'
import webpush from "npm:web-push"
import { createClient } from 'npm:@supabase/supabase-js@2'

type WebhookPayload = {
  type: 'INSERT' | 'UPDATE' | 'DELETE'
  schema: string
  table: string
  record: any
}

type WebPushSubscription = {
  endpoint: string
  keys: { p256dh: string; auth: string }
}

const VAPID_PUBLIC_KEY = Deno.env.get("VAPID_PUBLIC_KEY")
const VAPID_PRIVATE_KEY = Deno.env.get("VAPID_PRIVATE_KEY")
const PUSH_URL = Deno.env.get("WEBSITE_URL")

if (!VAPID_PUBLIC_KEY || !VAPID_PRIVATE_KEY) {
  throw new Error("Missing VAPID_PUBLIC_KEY or VAPID_PRIVATE_KEY")
}

webpush.setVapidDetails(
  PUSH_URL,
  VAPID_PUBLIC_KEY,
  VAPID_PRIVATE_KEY
)

Deno.serve(async (req: { method: string; json: () => WebhookPayload | PromiseLike<WebhookPayload> }) => {
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 })
  }

  const payload = (await req.json()) as WebhookPayload

  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!,
  )

  const { data: subscriptions, error } = await supabase.schema("forms")
    .from('Notification') // forms."Notification"
    .select('subscription')
    .limit(5000)

  if (error) {
    return new Response(JSON.stringify({ ok: false, error: error.message }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    })
  }

  const PushPayload = {
    title: payload?.record?.title ?? 'Notification',
    body: payload?.record?.description ?? '',
  }
  const subs = (subscriptions ?? []).map((r: any) => r.subscription) as WebPushSubscription[]
  const results = await Promise.allSettled(
    subs.map(async (sub: any) => webpush.sendNotification(
      sub as any,
      JSON.stringify(PushPayload))
    ))

  return new Response(
    JSON.stringify({
      ok: true,
      sent: results.filter((r: { status: string }) => r.status === "fulfilled").length,
      failed: results.filter((r: { status: string }) => r.status === "rejected").length,
    }),
    { headers: { "Content-Type": "application/json" } }
  )
})
