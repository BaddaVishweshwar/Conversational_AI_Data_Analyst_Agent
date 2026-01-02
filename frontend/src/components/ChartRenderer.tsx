import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ChartRendererProps {
    config: {
        type: string;
        data: any[];
        columns: string[];
        xAxis?: string;
        yAxis?: string[];
    };
}

const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4'];

export default function ChartRenderer({ config }: ChartRendererProps) {
    const { type, data, columns, xAxis, yAxis } = config;

    if (!data || data.length === 0) {
        return (
            <div className="text-center py-8 text-muted-foreground">
                No data to display
            </div>
        );
    }

    if (type === 'line') {
        return (
            <ResponsiveContainer width="100%" height={400}>
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey={xAxis || columns[0]} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    {(yAxis || columns.slice(1)).map((col, idx) => (
                        <Line
                            key={col}
                            type="monotone"
                            dataKey={col}
                            stroke={COLORS[idx % COLORS.length]}
                            strokeWidth={2}
                        />
                    ))}
                </LineChart>
            </ResponsiveContainer>
        );
    }

    if (type === 'bar') {
        return (
            <ResponsiveContainer width="100%" height={400}>
                <BarChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey={xAxis || columns[0]} />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    {(yAxis || columns.slice(1)).map((col, idx) => (
                        <Bar
                            key={col}
                            dataKey={col}
                            fill={COLORS[idx % COLORS.length]}
                        />
                    ))}
                </BarChart>
            </ResponsiveContainer>
        );
    }

    if (type === 'pie') {
        const pieData = data.map((item) => ({
            name: item[xAxis || columns[0]],
            value: item[yAxis?.[0] || columns[1]],
        }));

        return (
            <ResponsiveContainer width="100%" height={400}>
                <PieChart>
                    <Pie
                        data={pieData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        outerRadius={120}
                        fill="#8884d8"
                        dataKey="value"
                    >
                        {pieData.map((_entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip />
                </PieChart>
            </ResponsiveContainer>
        );
    }

    // Default to table view
    return (
        <div className="overflow-x-auto">
            <table className="w-full text-sm">
                <thead>
                    <tr className="border-b">
                        {columns.map((col) => (
                            <th key={col} className="text-left p-2 font-medium">
                                {col}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.slice(0, 50).map((row, idx) => (
                        <tr key={idx} className="border-b hover:bg-accent">
                            {columns.map((col) => (
                                <td key={col} className="p-2">
                                    {typeof row[col] === 'number'
                                        ? row[col].toLocaleString()
                                        : row[col]}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
            {data.length > 50 && (
                <p className="text-sm text-muted-foreground mt-2 text-center">
                    Showing first 50 of {data.length} rows
                </p>
            )}
        </div>
    );
}
