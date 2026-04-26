import { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import getApiErrorMessage from '../services/errorMessage';

const COLORS = [
  '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
  '#ec4899', '#06b6d4', '#f97316', '#6366f1', '#14b8a6',
];

export default function KnowledgeGraph({ uploadId }) {
  const [graph, setGraph] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [hoveredNode, setHoveredNode] = useState(null);
  const svgRef = useRef(null);

  const fetchGraph = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get(`/uploads/${uploadId}/knowledge-graph`);
      setGraph(res.data);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Failed to generate knowledge graph'));
    } finally {
      setLoading(false);
    }
  };

  if (!graph && !loading && !error) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400 mb-4">Generate a knowledge graph from this material</p>
        <button
          onClick={fetchGraph}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
        >
          Generate Knowledge Graph
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-gray-500 dark:text-gray-400 mt-3">Generating knowledge graph...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500 mb-4">{error}</p>
        <button onClick={fetchGraph} className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition">
          Retry
        </button>
      </div>
    );
  }

  const nodes = graph?.nodes || [];
  const edges = graph?.edges || [];
  const groups = [...new Set(nodes.map((n) => n.group))];
  const groupColorMap = {};
  groups.forEach((g, i) => { groupColorMap[g] = COLORS[i % COLORS.length]; });

  // Simple force-directed layout (static positions)
  const width = 800;
  const height = 500;
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(width, height) * 0.35;

  const nodePositions = {};
  nodes.forEach((node, i) => {
    const angle = (2 * Math.PI * i) / nodes.length;
    nodePositions[node.id] = {
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
    };
  });

  return (
    <div>
      <div className="flex gap-4 mb-4 flex-wrap">
        {groups.map((g) => (
          <span key={g} className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400">
            <span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: groupColorMap[g] }}></span>
            {g}
          </span>
        ))}
        <button onClick={fetchGraph} className="ml-auto text-xs text-blue-600 dark:text-blue-400 hover:underline">
          Regenerate
        </button>
      </div>

      <svg ref={svgRef} viewBox={`0 0 ${width} ${height}`} className="w-full border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-900">
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#9ca3af" />
          </marker>
        </defs>

        {/* Edges */}
        {edges.map((edge, i) => {
          const from = nodePositions[edge.source];
          const to = nodePositions[edge.target];
          if (!from || !to) return null;
          const midX = (from.x + to.x) / 2;
          const midY = (from.y + to.y) / 2 - 10;
          return (
            <g key={`edge-${i}`}>
              <line x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke="#9ca3af" strokeWidth="1.5" markerEnd="url(#arrowhead)" opacity="0.6" />
              {edge.label && (
                <text x={midX} y={midY} textAnchor="middle" fontSize="9" fill="#9ca3af" className="select-none">
                  {edge.label}
                </text>
              )}
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map((node) => {
          const pos = nodePositions[node.id];
          if (!pos) return null;
          const color = groupColorMap[node.group] || '#6b7280';
          const isHovered = hoveredNode === node.id;
          return (
            <g
              key={node.id}
              onMouseEnter={() => setHoveredNode(node.id)}
              onMouseLeave={() => setHoveredNode(null)}
              className="cursor-pointer"
            >
              <circle cx={pos.x} cy={pos.y} r={isHovered ? 22 : 18} fill={color} opacity={isHovered ? 1 : 0.8} />
              <text x={pos.x} y={pos.y + 30} textAnchor="middle" fontSize="10" fill="currentColor" className="select-none dark:fill-gray-300 fill-gray-700">
                {node.label.length > 15 ? node.label.slice(0, 15) + '...' : node.label}
              </text>
              {isHovered && (
                <text x={pos.x} y={pos.y - 28} textAnchor="middle" fontSize="11" fontWeight="bold" fill="currentColor" className="dark:fill-gray-100 fill-gray-900">
                  {node.label}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
