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
    hooks: {
      onBrokenMarkdownLinks: "warn",
    },
  },

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
        },
        blog: {
          showReadingTime: true,
          blogTitle: "Journal",
          blogDescription: "Engineering notes, changes, and write-ups",
          blogSidebarTitle: "Recent posts",
          blogSidebarCount: 10,
          editUrl:
            "https://github.com/newcomb-labs/engineering-journal-kb/tree/main/",
        },
        theme: {
          customCss: require.resolve("./src/css/custom.css"),
        },
      },
    ],
  ],

  themeConfig: {
    image: "img/social-card.jpg",
    navbar: {
      title: "Engineering Journal",
      logo: {
        alt: "Engineering Journal Logo",
        src: "img/logo.svg",
      },
      items: [
        { to: "/docs/intro", label: "Docs", position: "left" },
        { to: "/blog", label: "Journal", position: "left" },
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
            { label: "Journal", to: "/blog" },
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
  },
};

module.exports = config;
