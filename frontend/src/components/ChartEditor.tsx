import React from 'react';
import { Button } from './ui/button';
import { Settings2, Check, X } from 'lucide-react';

interface ChartEditorProps {
    config: any;
    onSave: (newConfig: any) => void;
    onCancel: () => void;
}

export default function ChartEditor({ config, onSave, onCancel }: ChartEditorProps) {
    const [tempConfig, setTempConfig] = React.useState({ ...config });

    const chartTypes = ['line', 'bar', 'pie', 'table'];
    const columns: string[] = config.columns || [];

    const handleChange = (field: string, value: any) => {
        setTempConfig((prev: any) => ({ ...prev, [field]: value }));
    };

    return (
        <div className="bg-muted/30 p-4 rounded-lg border border-primary/20 space-y-4 animate-in fade-in slide-in-from-top-2">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Settings2 className="w-4 h-4 text-primary" />
                    <h4 className="text-sm font-bold uppercase tracking-wider">Visual Chart Tuner</h4>
                </div>
                <div className="flex gap-2">
                    <Button size="sm" variant="ghost" onClick={onCancel} className="h-7 w-7 p-0">
                        <X className="w-4 h-4 text-destructive" />
                    </Button>
                    <Button size="sm" onClick={() => onSave(tempConfig)} className="h-7 px-3 bg-primary text-white text-[10px] font-bold">
                        <Check className="w-3 h-3 mr-1" /> APPLY
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-tight">Chart Type</label>
                    <select
                        value={tempConfig.type}
                        onChange={(e) => handleChange('type', e.target.value)}
                        className="w-full h-8 px-2 text-xs bg-background border rounded-md focus:ring-2 focus:ring-primary outline-none uppercase"
                    >
                        {chartTypes.map(t => (
                            <option key={t} value={t}>{t}</option>
                        ))}
                    </select>
                </div>

                <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-tight">X-Axis (Label)</label>
                    <select
                        value={tempConfig.xAxis || columns[0]}
                        onChange={(e) => handleChange('xAxis', e.target.value)}
                        className="w-full h-8 px-2 text-xs bg-background border rounded-md focus:ring-2 focus:ring-primary outline-none"
                    >
                        {columns.map(c => (
                            <option key={c} value={c}>{c}</option>
                        ))}
                    </select>
                </div>

                {tempConfig.type !== 'pie' && (
                    <div className="space-y-1.5">
                        <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-tight">Y-Axis (Metrics)</label>
                        <div className="flex flex-wrap gap-1">
                            {columns.map(c => {
                                const currentY: string[] = tempConfig.yAxis || columns.slice(1);
                                const isSelected = currentY.includes(c);
                                return (
                                    <button
                                        key={c}
                                        onClick={() => {
                                            const newY = currentY.includes(c)
                                                ? currentY.filter((y: string) => y !== c)
                                                : [...currentY, c];
                                            handleChange('yAxis', newY);
                                        }}
                                        className={`px-2 py-0.5 rounded text-[10px] border transition-all ${isSelected
                                            ? 'bg-primary/10 border-primary text-primary font-bold'
                                            : 'bg-muted border-transparent text-muted-foreground opacity-60'
                                            }`}
                                    >
                                        {c}
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
