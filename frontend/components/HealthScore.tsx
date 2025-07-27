import React from 'react';
import { Agent } from '../types';
import { UserCircleIcon } from './IconComponents';

const agents: Agent[] = [
    { id: '1', name: 'Budget Bot', role: 'Expense Tracker', avatar: UserCircleIcon, status: 'Active' },
    { id: '2', name: 'Savings Sage', role: 'Goal Planner', avatar: UserCircleIcon, status: 'Active' },
    { id: '3', name: 'Debt Destroyer', role: 'Loan Manager', avatar: UserCircleIcon, status: 'Active' },
    { id: '4', name: 'Market Maven', role: 'Investment Analyst', avatar: UserCircleIcon, status: 'Inactive' },
];

const AgentRow: React.FC<{ agent: Agent }> = ({ agent }) => (
    <div className="flex items-center justify-between p-3 hover:bg-zinc-700/50 rounded-lg transition-colors">
        <div className="flex items-center gap-4">
            <div className="w-10 h-10 flex items-center justify-center bg-zinc-700 rounded-full p-1">
                 <agent.avatar className="w-8 h-8 accent-color" />
            </div>
            <div>
                <p className="font-semibold text-white">{agent.name}</p>
                <p className="text-sm text-zinc-400">{agent.role}</p>
            </div>
        </div>
        <div className="flex items-center gap-2">
            <div className={`w-2.5 h-2.5 rounded-full ${agent.status === 'Active' ? 'bg-green-500' : 'bg-zinc-500'}`}></div>
            <p className={`text-sm font-medium ${agent.status === 'Active' ? 'text-green-400' : 'text-zinc-500'}`}>{agent.status}</p>
        </div>
    </div>
);


const AgentsStatus: React.FC = () => {
    return (
        <div className="bg-zinc-800/50 p-6 rounded-lg h-full flex flex-col">
            <h2 className="text-lg font-semibold text-white mb-4">Agents Status</h2>
             <div className="space-y-2 -m-3">
                {agents.map(agent => <AgentRow key={agent.id} agent={agent} />)}
            </div>
        </div>
    );
};

export default AgentsStatus;