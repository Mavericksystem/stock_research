import { useEffect, type ReactNode } from "react";

import Footer from "../../layouts/Footer";

/**
 * Optional. When set at build time (VITE_PRIVACY_CONTACT_EMAIL) the "Contact"
 * section is rendered; when unset it is omitted rather than shipping a
 * placeholder address.
 */
const CONTACT_EMAIL = (import.meta.env.VITE_PRIVACY_CONTACT_EMAIL as string | undefined)?.trim();

const LAST_UPDATED = "September 23, 2026";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mt-8">
      <h2 className="mb-2 text-[15px] font-semibold text-[var(--text)]">{title}</h2>
      <div className="space-y-3 text-[14px] leading-[1.7] text-[var(--text-muted)]">{children}</div>
    </section>
  );
}

export default function PrivacyPage() {
  useEffect(() => {
    const previous = document.title;
    document.title = "Privacy Policy · Market Mind";
    return () => {
      document.title = previous;
    };
  }, []);

  return (
    <div className="flex h-dvh flex-col overflow-y-auto bg-[var(--bg)] text-[var(--text)]">
      <main id="main-content" className="mx-auto w-full max-w-[720px] flex-1 px-5 py-10 md:py-16">
        <a
          href="/"
          className="font-mono text-[12px] text-[var(--text-muted)] underline-offset-4 hover:text-[var(--text)] hover:underline"
        >
          ← Back to Market Mind
        </a>

        <h1 className="mt-6 text-[26px] font-semibold tracking-[-0.5px]">Privacy Policy</h1>
        <p className="mt-1 font-mono text-[12px] text-[var(--text-dim)]">
          Last updated {LAST_UPDATED}
        </p>

        <p className="mt-6 text-[14px] leading-[1.7] text-[var(--text-muted)]">
          Market Mind explains why a stock moved. There are no accounts, no sign-up and no
          advertising. This page describes the limited data involved when you use the site.
        </p>

        <Section title="What we collect">
          <p>
            <strong className="font-medium text-[var(--text)]">Your questions.</strong> When you ask
            a question, the text and the ticker symbol are sent to our API to generate an answer.
            They are not tied to any account or identity and are not saved to our database.
          </p>
          <p>
            <strong className="font-medium text-[var(--text)]">Server logs.</strong> Our hosting
            providers automatically log basic request data — IP address, timestamp, requested URL
            and browser user agent — for security and operations. We do not use this data to
            identify or profile visitors.
          </p>
        </Section>

        <Section title="Cookies and local storage">
          <p>
            Market Mind does not set cookies. We do not use analytics, advertising or tracking
            technologies.
          </p>
        </Section>

        <Section title="Third parties that process data">
          <ul className="list-disc space-y-2 pl-5">
            <li>
              <strong className="font-medium text-[var(--text)]">Vercel</strong> serves the website
              and <strong className="font-medium text-[var(--text)]">Render</strong> hosts the API.
              Both process request data (including IP addresses) to deliver the service.
            </li>
            <li>
              <strong className="font-medium text-[var(--text)]">NVIDIA NIM</strong> — the language
              model that writes explanations. Your question text is sent to it to produce an answer.
              Please do not enter personal or confidential information into questions.
            </li>
            <li>
              <strong className="font-medium text-[var(--text)]">Google Fonts</strong> — fonts are
              loaded from Google&apos;s servers, so Google receives your IP address and browser
              details when a page loads.
            </li>
          </ul>
        </Section>

        <Section title="Data retention">
          <p>
            Questions are not retained by us. Server logs are kept by our hosting providers under
            their own retention schedules.
          </p>
        </Section>

        <Section title="Your rights">
          <p>
            Depending on where you live (for example under the GDPR or CCPA), you may have the
            right to access, correct or delete personal data held about you, or to object to its
            processing. Because we do not hold account or profile data, the only personal data
            involved is the log data described above, which sits with our hosting providers; you
            can also contact them directly.
          </p>
        </Section>

        <Section title="Children">
          <p>Market Mind is not directed at children under 16 and does not knowingly collect their data.</p>
        </Section>

        <Section title="Changes to this policy">
          <p>
            If we add features that change how data is handled (for example accounts or analytics),
            we will update this page and the date above before they go live.
          </p>
        </Section>

        {CONTACT_EMAIL && (
          <Section title="Contact">
            <p>
              Questions about this policy or a data request:{" "}
              <a
                href={`mailto:${CONTACT_EMAIL}`}
                className="text-[var(--amber)] underline-offset-4 hover:underline"
              >
                {CONTACT_EMAIL}
              </a>
            </p>
          </Section>
        )}
      </main>

      <Footer />
    </div>
  );
}
