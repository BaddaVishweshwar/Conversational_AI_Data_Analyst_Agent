import Editor from '@monaco-editor/react';
import { Button } from './ui/button';
import { Play } from 'lucide-react';
import { useState } from 'react';

interface SQLEditorProps {
    initialValue: string;
    onRun: (sql: string) => void;
}

export default function SQLEditor({ initialValue, onRun }: SQLEditorProps) {
    const [sql, setSql] = useState(initialValue);

    return (
        <div className="border rounded-lg overflow-hidden bg-background mb-4">
            <div className="flex items-center justify-between px-4 py-2 bg-muted/50 border-b">
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                    <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">SQL Workpad</span>
                </div>
                <Button
                    size="sm"
                    onClick={() => onRun(sql)}
                    className="h-7 gap-2 px-4 bg-primary hover:bg-primary/90 text-white font-bold transition-all transform active:scale-95"
                >
                    <Play className="w-3 h-3" />
                    EXCUTE
                </Button>
            </div>
            <div className="h-[200px] border-b">
                <Editor
                    height="100%"
                    defaultLanguage="sql"
                    value={sql}
                    theme="vs-dark"
                    onChange={(val) => setSql(val || "")}
                    options={{
                        minimap: { enabled: false },
                        scrollBeyondLastLine: false,
                        fontSize: 13,
                        wordWrap: "on",
                        lineNumbers: "on",
                        automaticLayout: true,
                        fontFamily: "'Fira Code', 'Monaco', 'Cascadia Code', monospace"
                    }}
                />
            </div>
            <div className="px-4 py-1 bg-muted/30 flex justify-between">
                <span className="text-[10px] text-muted-foreground italic">Powered by Monaco Engine</span>
                <span className="text-[10px] text-muted-foreground">{sql.length} characters</span>
            </div>
        </div>
    );
}
