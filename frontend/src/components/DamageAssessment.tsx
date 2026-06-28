import React from 'react';

interface DamageAssessmentProps {
  impact: {
    hazard_type: string;
    severity_score: number;
    estimated_impact: {
      population_affected: number;
      buildings_damaged: number;
      roads_blocked_km: number;
      economic_loss_usd: number;
    };
    critical_infrastructure_at_risk: { type: string; status: string }[];
  } | null;
  lang?: string;
}

const formatCurrency = (val: number) => {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(1)}M`;
  if (val >= 1000) return `$${(val / 1000).toFixed(1)}K`;
  return `$${val}`;
};

const DamageAssessment: React.FC<DamageAssessmentProps> = ({ impact, lang = 'en' }) => {
  if (!impact) return null;

  return (
    <div className="bg-red-900 bg-opacity-20 border border-red-800 p-4 rounded-lg mt-4 text-white">
      <h3 className="text-xl font-bold text-red-400 mb-3 flex items-center">
        <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
        Damage Assessment
      </h3>
      
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-gray-800 p-3 rounded border border-gray-700">
          <p className="text-gray-400 text-xs uppercase tracking-wider">Affected Pop.</p>
          <p className="text-2xl font-bold text-yellow-500">{impact.estimated_impact.population_affected.toLocaleString()}</p>
        </div>
        <div className="bg-gray-800 p-3 rounded border border-gray-700">
          <p className="text-gray-400 text-xs uppercase tracking-wider">Econ Loss</p>
          <p className="text-2xl font-bold text-red-500">{formatCurrency(impact.estimated_impact.economic_loss_usd)}</p>
        </div>
        <div className="bg-gray-800 p-3 rounded border border-gray-700">
          <p className="text-gray-400 text-xs uppercase tracking-wider">Buildings Damaged</p>
          <p className="text-lg font-semibold">{impact.estimated_impact.buildings_damaged.toLocaleString()}</p>
        </div>
        <div className="bg-gray-800 p-3 rounded border border-gray-700">
          <p className="text-gray-400 text-xs uppercase tracking-wider">Roads Blocked</p>
          <p className="text-lg font-semibold">{impact.estimated_impact.roads_blocked_km.toFixed(1)} km</p>
        </div>
      </div>

      {impact.critical_infrastructure_at_risk.length > 0 && (
        <div className="mt-3">
          <p className="text-sm font-semibold text-red-300 mb-2">Critical Infrastructure at Risk:</p>
          <ul className="space-y-1">
            {impact.critical_infrastructure_at_risk.map((infra, idx) => (
              <li key={idx} className="flex justify-between items-center bg-gray-800 px-3 py-2 rounded text-sm">
                <span className="font-medium">{infra.type}</span>
                <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                  infra.status.includes('Offline') || infra.status.includes('Compromised') 
                    ? 'bg-red-500 text-white' 
                    : 'bg-yellow-500 text-black'
                }`}>{infra.status}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default DamageAssessment;
