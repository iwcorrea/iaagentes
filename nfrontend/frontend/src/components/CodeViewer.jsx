import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import api from '../api/axios';
export default function CodeViewer({ file, project }) {
  const [code, setCode] = React.useState('');
  React.useEffect(() => {
    if (file && project) {
      api.get(`/projects/${project.id}/files/${file.id}`)
        .then(res => setCode(res.data.content))
        .catch(err => setCode('Error loading file content'));
    }
  }, [file, project]);
  if (!file) return <div className="flex-1 flex items-center justify-center text-slate-500">Select a file to view code</div>;
  return (
    <div className="flex-1 overflow-hidden flex flex-col">
      <div className="p-2 bg-brand-surface border-b border-brand-border text-xs font-mono text-slate-400">
        {file.name}
      </div>
      <div className="flex-1 overflow-auto custom-scrollbar">
        <SyntaxHighlighter 
          language="javascript" 
          style={vscDarkPlus} 
          customStyle={{ margin: 0, height: '100%', fontSize: '13px' }}
        >
          {code}
        </SyntaxHighlighter>
      </div>
    </div>
  );
}