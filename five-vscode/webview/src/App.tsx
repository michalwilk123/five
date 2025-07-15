import { useState } from "react";
import "@vscode-elements/elements/dist/vscode-tabs";
import "@vscode-elements/elements/dist/vscode-tab-header";
import "@vscode-elements/elements/dist/vscode-tab-panel";
import { AgentCodeTab } from "./components/AgentCodeTab";
import { RecipeTab } from "./components/RecipeTab";
import { SettingsTab } from "./components/SettingsTab";

if (import.meta.env.DEV) {
  await import("@vscode-elements/webview-playground");
}

function App() {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <>
      {import.meta.env.DEV ? <vscode-dev-toolbar></vscode-dev-toolbar> : null}
      <vscode-tabs
        selected-index={activeTab}
        onvsc-tabs-select={e => setActiveTab(e.detail.selectedIndex)}
      >
        <vscode-tab-header slot="header">Agent / Code</vscode-tab-header>
        <vscode-tab-panel>
          <AgentCodeTab />
        </vscode-tab-panel>
        <vscode-tab-header slot="header">Recipe</vscode-tab-header>
        <vscode-tab-panel>
          <RecipeTab />
        </vscode-tab-panel>
        <vscode-tab-header slot="header">Settings</vscode-tab-header>
        <vscode-tab-panel>
          <SettingsTab />
        </vscode-tab-panel>
      </vscode-tabs>
    </>
  );
}

export default App;