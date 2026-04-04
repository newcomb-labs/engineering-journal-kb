const { themes: prismThemes } = require("prism-react-renderer");

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "Engineering Journal",
  tagline: "Docs, journal entries, and governance notes",
  favicon: "img/favicon.ico",

  url: "https://newcomb-labs.github.io",
  baseUrl: "/engineering-journal-kb/",

  organizationName: "newcomb-labs",
  projectName: "engineering-journal-kb",
  deploymentBranch: "gh-pages",
  trailingSlash: false,

  onBrokenLinks: "throw",

  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: "warn",
    },
  },
  themes: ["@docusaurus/theme-mermaid"],

  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  presets: [
    [
      "classic",
      {
        docs: {
          sidebarPath: require.resolve("./sidebars.js"),
          routeBasePath: "docs",
          editUrl:
            "https://github.com/newcomb-labs/engineering-journal-kb/tree/main/",
          showLastUpdateAuthor: true,
          showLastUpdateTime: true,
        },
        blog: false,
        theme: {
          customCss: require.resolve("./src/css/custom.css"),
        },
      },
    ],
  ],

  themeConfig: {
    image: "img/social-card.jpg",

    colorMode: {
      defaultMode: "dark",
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },

    navbar: {
      title: "Engineering Journal",
      logo: {
        alt: "Engineering Journal Logo",
        src: "img/logo.svg",
      },
      items: [
        { to: "/docs/intro", label: "Docs", position: "left" },
        { to: "/docs/journal", label: "Journal", position: "left" },
        {
          href: "https://github.com/newcomb-labs/engineering-journal-kb",
          label: "GitHub",
          position: "right",
        },
      ],
    },

    footer: {
      style: "dark",
      links: [
        {
          title: "Content",
          items: [
            { label: "Docs", to: "/docs/intro" },
            { label: "Journal", to: "/docs/journal" },
          ],
        },
        {
          title: "More",
          items: [
            {
              label: "GitHub",
              href: "https://github.com/newcomb-labs/engineering-journal-kb",
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Chris Newcomb`,
    },

    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },

    docs: {
      sidebar: {
        hideable: true,
        autoCollapseCategories: true,
      },
    },
  },
};

module.exports = config;
