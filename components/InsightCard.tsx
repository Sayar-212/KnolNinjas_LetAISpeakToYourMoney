
import React, { useState, useEffect, useCallback } from 'react';
import { LightbulbIcon, RefreshIcon } from './IconComponents';
import { getOneTimeInsight } from '../services/geminiService';

const InsightCard: React.FC = () => {
    const [insight, setInsight] = useState('');
    const [isLoading, setIsLoading] = useState(true);

    const fetchInsight = useCallback(async () => {
        setIsLoading(true);
        const prompt = "Give me one key financial insight for a typical person in their 20s or 30s. Focus on a practical, actionable tip related to budgeting, saving, or debt management. For example, 'Automating your savings...' or 'The 50/30/20 rule...'. Keep it to a single paragraph.";
        const result = await getOneTimeInsight(prompt);
        setInsight(result);
        setIsLoading(false);
    }, []);

    useEffect(() => {
        fetchInsight();
    }, [fetchInsight]);

    return (
        <div className="bg-zinc-800/50 p-6 rounded-lg h-full flex flex-col">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h2 className="text-lg font-semibold text-white">AI Insight</h2>
                     <p className="text-sm text-zinc-400">A tip from your co-pilot.</p>
                </div>
                <div className="flex items-center gap-2">
                    <LightbulbIcon className="w-6 h-6 text-amber-400" />
                    <button onClick={fetchInsight} disabled={isLoading} className="text-zinc-400 hover:text-white disabled:text-zinc-600 disabled:cursor-wait">
                        <RefreshIcon className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
            </div>
            <div className="flex-grow flex items-center justify-center">
                {isLoading ? (
                     <div className="text-zinc-400 text-sm">Generating insight...</div>
                ) : (
                    <p className="text-zinc-300 leading-relaxed">
                        {insight}
                    </p>
                )}
            </div>
        </div>
    );
};

export default InsightCard;
