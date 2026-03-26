import React from "react";
import clsx from "clsx";
import Link from "@docusaurus/Link";
import Layout from "@theme/Layout";
import Heading from "@theme/Heading";

import styles from "./index.module.css";

const features = [
  {
    title: "Documentation",
    description:
      "Structured reference material, procedures, and evergreen technical notes.",
    link: "/docs/intro",
    linkLabel: "Open Docs",
    icon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M7 3.75h7.5L19 8.25V20.25a1.5 1.5 0 0 1-1.5 1.5h-10A1.5 1.5 0 0 1 6 20.25V5.25a1.5 1.5 0 0 1 1.5-1.5Z" />
        <path d="M14.5 3.75v4.5H19" />
        <path d="M9 12h6" />
        <path d="M9 15.5h6" />
      </svg>
    ),
  },
  {
    title: "Labs",
    description:
      "Hands-on exercises, reproducible walkthroughs, and implementation notes from real practice.",
    link: "/docs/labs",
    linkLabel: "View Labs",
    icon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M10 3.75v5.5l-4.75 8.25a2 2 0 0 0 1.73 3h10.04a2 2 0 0 0 1.73-3L14 9.25v-5.5" />
        <path d="M8.25 3.75h7.5" />
        <path d="M8.5 14.5h7" />
      </svg>
    ),
  },
  {
    title: "Case Studies",
    description:
      "Troubleshooting write-ups, root cause analysis, and lessons learned from applied engineering work.",
    link: "/docs/case-studies",
    linkLabel: "Read Case Studies",
    icon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M10.5 18.75A8.25 8.25 0 1 1 18.75 10.5" />
        <path d="m21 21-4.35-4.35" />
        <path d="M9 10.5h3.75v3.75" />
      </svg>
    ),
  },
  {
    title: "Journal",
    description:
      "Engineering notes, updates, and working history that document progress over time.",
    link: "/blog",
    linkLabel: "Read Journal",
    icon: (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M6.75 4.5h10.5A1.75 1.75 0 0 1 19 6.25v11A1.75 1.75 0 0 1 17.25 19H6.75A1.75 1.75 0 0 1 5 17.25v-11A1.75 1.75 0 0 1 6.75 4.5Z" />
        <path d="M8.5 8h7" />
        <path d="M8.5 11.5h7" />
        <path d="M8.5 15h4.5" />
      </svg>
    ),
  },
];

function HomepageHeader() {
  return (
    <header className={clsx("hero hero--primary", styles.heroBanner)}>
      <div className={styles.heroPattern} />
      <div className={clsx("container", styles.heroInner)}>
        <div className={styles.heroGrid}>
          <div>
            <p className={styles.kicker}>ENGINEERING JOURNAL</p>
            <Heading as="h1" className={styles.heroTitle}>
              Docs, labs, case studies, and governance notes in one place.
            </Heading>
            <p className={styles.heroSubtitle}>
              A technical knowledge base for documenting hands-on work,
              reproducible lab exercises, troubleshooting analysis, and the
              systems that keep engineering work organized.
            </p>

            <div className={styles.heroActions}>
              <Link
                className="button button--primary button--lg"
                to="/docs/intro"
              >
                Open Docs
              </Link>
              <Link className="button button--secondary button--lg" to="/blog">
                Read Journal
              </Link>
            </div>
          </div>

          <div className={styles.heroPanel}>
            <div className={styles.panelHeader}>journal://overview</div>
            <div className={styles.panelBody}>
              <div className={styles.panelRow}>
                <span>Status</span>
                <span>Active</span>
              </div>
              <div className={styles.panelRow}>
                <span>Focus</span>
                <span>Docs + Labs + Governance</span>
              </div>
              <div className={styles.panelRow}>
                <span>Format</span>
                <span>Docusaurus Knowledge Base</span>
              </div>
              <div className={styles.panelRow}>
                <span>Content</span>
                <span>Technical Notes / Case Studies</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

function FeatureCard({ title, description, link, linkLabel, icon }) {
  return (
    <div className={clsx("col col--6")}>
      <div className={styles.card}>
        <div className={styles.cardIconWrap}>
          <div className={styles.cardIcon}>{icon}</div>
        </div>
        <Heading as="h2" className={styles.cardTitle}>
          {title}
        </Heading>
        <p className={styles.cardDescription}>{description}</p>
        <Link className={styles.cardLink} to={link}>
          {linkLabel} →
        </Link>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <Layout
      title="Home"
      description="Engineering Journal knowledge base with documentation, labs, case studies, and governance notes."
    >
      <HomepageHeader />
      <main>
        <section className={styles.section}>
          <div className="container">
            <div className={styles.sectionHeading}>
              <Heading as="h2">Explore the journal</Heading>
              <p>
                Built to capture technical work clearly, preserve context, and
                make it easier to revisit what was done and why.
              </p>
            </div>

            <div className="row">
              {features.map((feature) => (
                <FeatureCard key={feature.title} {...feature} />
              ))}
            </div>
          </div>
        </section>

        <section className={styles.sectionAlt}>
          <div className="container">
            <div className={styles.callout}>
              <Heading as="h2">Why this site exists</Heading>
              <p>
                Good engineering work gets lost fast when it lives in scattered
                notes, terminal history, screenshots, and half-remembered fixes.
                This journal turns that work into durable documentation.
              </p>
              <ul className={styles.calloutList}>
                <li>Document repeatable workflows</li>
                <li>Preserve troubleshooting context</li>
                <li>Capture lessons learned from labs and incidents</li>
                <li>Track governance, CI, and repo standards over time</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
