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
    {
      type: "doc",
      id: "labs/vm-cloning-auth-failure-lab",
      label: "VM Cloning Failure Lab",
    },
    {
      type: "doc",
      id: "case-studies/vm-cloning-auth-failure",
      label: "VM Cloning Failure Case Study",
    },
  ],
};

module.exports = sidebars;
