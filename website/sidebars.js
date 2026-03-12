/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docsSidebar: [
    "intro",
    {
      type: "category",
      label: "Engineering",
      items: ["engineering/architecture", "engineering/automation"],
    },
    {
      type: "category",
      label: "Operations",
      items: ["operations/runbooks", "operations/incident-response"],
    },
    {
      type: "category",
      label: "Governance",
      items: ["governance/repo-standards", "governance/commit-policy"],
    },
  ],
};

module.exports = sidebars;
