
import React from 'react';
import { Bill } from '../types';
import { NetflixIcon, SpotifyIcon, UtilityIcon } from './IconComponents';

const bills: Bill[] = [
    { id: '1', name: 'Netflix Subscription', amount: 15.49, dueDate: '28 Jun', icon: NetflixIcon },
    { id: '2', name: 'Spotify Premium', amount: 10.99, dueDate: '30 Jun', icon: SpotifyIcon },
    { id: '3', name: 'Electricity Bill', amount: 75.20, dueDate: '05 Jul', icon: UtilityIcon },
    { id: '4', name: 'Internet Bill', amount: 59.99, dueDate: '10 Jul', icon: () => <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold text-sm">ISP</div> },
];

const getDueDateInfo = (dueDateStr: string): { text: string; color: string } => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const dueDate = new Date(`${dueDateStr} ${today.getFullYear()}`);
    dueDate.setHours(0, 0, 0, 0);

    if (dueDate < today) {
        const nextYearDueDate = new Date(dueDate);
        nextYearDueDate.setFullYear(today.getFullYear() + 1);
        if(Math.abs(new Date().getTime() - dueDate.getTime()) > 1000 * 60 * 60 * 24 * 30 * 6) { // if due date was more than 6 months ago, assume next year
             dueDate.setFullYear(today.getFullYear() + 1);
        }
    }

    const diffTime = dueDate.getTime() - today.getTime();
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
        return { text: `Overdue by ${Math.abs(diffDays)}d`, color: "text-red-400" };
    }
    if (diffDays === 0) {
        return { text: "Due today", color: "text-amber-400" };
    }
    if (diffDays === 1) {
        return { text: "Due tomorrow", color: "text-amber-400" };
    }
    if (diffDays <= 7) {
        return { text: `Due in ${diffDays}d`, color: "text-yellow-300" };
    }
    return { text: `Due ${dueDateStr}`, color: "text-zinc-400" };
};


const BillRow: React.FC<{ bill: Bill }> = ({ bill }) => {
    const dueDateInfo = getDueDateInfo(bill.dueDate);
    return (
        <div className="flex items-center justify-between p-3 hover:bg-zinc-700/50 rounded-lg transition-colors">
            <div className="flex items-center gap-4">
                <div className="w-10 h-10 flex items-center justify-center bg-zinc-700 rounded-full p-1">
                     <bill.icon className="w-6 h-6 text-white" />
                </div>
                <div>
                    <p className="font-semibold text-white">{bill.name}</p>
                    <p className={`text-sm font-medium ${dueDateInfo.color}`}>{dueDateInfo.text}</p>
                </div>
            </div>
            <div className="text-right">
                <p className="font-semibold text-white">${bill.amount.toFixed(2)}</p>
            </div>
        </div>
    );
};

const UpcomingBills: React.FC = () => {
    return (
        <div className="bg-zinc-800/50 p-6 rounded-lg">
            <h2 className="text-lg font-semibold text-white mb-4">Upcoming Bills</h2>
            <div className="space-y-2 -m-3">
                {bills.map(bill => <BillRow key={bill.id} bill={bill} />)}
            </div>
        </div>
    );
};

export default UpcomingBills;
