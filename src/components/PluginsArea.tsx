import type { PluginManifest } from "../types";

type Props = {
  plugins: PluginManifest[];
};

export default function PluginsArea({ plugins }: Props) {
  if (!plugins.length) {
    return <p className="pill warn">No plugins discovered under /plugins</p>;
  }
  return (
    <div>
      {plugins.map((plugin) => (
        <div className="plugin-card" key={plugin.id || plugin.name}>
          <div className="name">{plugin.name || plugin.id}</div>
          <div className="meta">{plugin.description || "Shared Agent Builder plugin"}</div>
          {plugin.version ? <div className="pill">v{plugin.version}</div> : null}
        </div>
      ))}
    </div>
  );
}
