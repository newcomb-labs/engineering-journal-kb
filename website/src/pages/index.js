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
  },
  {
    title: "Labs",
    description:
      "Hands-on exercises, reproducible walkthroughs, and implementation notes from real practice.",
    link: "/docs/labs",
    linkLabel: "View Labs",
  },
  {
    title: "Case Studies",
    description:
      "Troubleshooting write-ups, root cause analysis, and lessons learned from applied engineering work.",
    link: "/docs/case-studies",
    linkLabel: "Read Case Studies",
  },
  {
    title: "Journal",
    description:
      "Engineering notes, updates, and working history that document progress over time.",
    link: "/blog",
    linkLabel: "Read Journal",
  },
];

function HomepageHeader() {
  return (
    <header className={clsx("hero hero--primary", styles.heroBanner)}>
      <div className="container">
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

function FeatureCard({ title, description, link, linkLabel }) {
  return (
    <div className={clsx("col col--6")}>
      <div className={styles.card}>
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
