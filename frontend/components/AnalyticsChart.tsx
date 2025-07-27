import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AnalyticsData } from '../types';

const data: AnalyticsData[] = [
    { name: 'Jan', income: 4000, expense: 2400 },
    { name: 'Feb', income: 3000, expense: 1398 },
    { name: 'Mar', income: 2000, expense: 9800 },
    { name: 'Apr', income: 2780, expense: 3908 },
    { name: 'May', income: 1890, expense: 4800 },
    { name: 'Jun', income: 2390, expense: 3800 },
];

const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-zinc-700 p-2 border border-zinc-600 rounded-md">
        <p className="font-bold text-white">{label}</p>
        <p className="accent-color">{`Income: $${payload[0].value}`}</p>
        <p className="text-amber-400">{`Expense: $${payload[1].value}`}</p>
      </div>
    );
  }
  return null;
};


const AnalyticsChart: React.FC = () => {
    return (
        <div className="bg-zinc-800/50 p-6 rounded-lg h-full">
            <h2 className="text-lg font-semibold text-white mb-4">Cash Flow</h2>
            <div className="w-full h-72">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                        <XAxis dataKey="name" stroke="#999" fontSize={12} />
                        <YAxis stroke="#999" fontSize={12} tickFormatter={(value) => `$${value/1000}k`}/>
                        <Tooltip content={<CustomTooltip />} cursor={{fill: 'rgba(100,100,100,0.1)'}} />
                        <Legend iconType="circle" iconSize={8} />
                        <Bar dataKey="income" fill="rgb(var(--color-accent-rgb))" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="expense" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default AnalyticsChart;