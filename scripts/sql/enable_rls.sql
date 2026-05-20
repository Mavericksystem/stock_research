-- Enable RLS (deny-by-default) on public tables exposed via PostgREST.
-- With RLS enabled and NO policies defined, anon/authenticated roles cannot read/write.
-- Backend connections using an owner/superuser/service-role-style access can still operate.

ALTER TABLE public.stocks               ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.prices               ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.technical_indicators ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.events               ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.news                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.event_news_link      ENABLE ROW LEVEL SECURITY;
