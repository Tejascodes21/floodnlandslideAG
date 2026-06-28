import React from 'react';

interface ExplainabilityPanelProps {
  explainabilityData: any;
  lang?: string;
}

const ExplainabilityPanel: React.FC<ExplainabilityPanelProps> = ({ explainabilityData, lang = 'en' }) => {
  if (!explainabilityData) return null;

  const { explanation, waterfall, top_drivers, prediction_probability, hazard_type } = explainabilityData;

  // Simple render for the explanation text (which is pre-formatted with newlines)
  const explanationLines = explanation ? explanation.split('\n') : [];

  return (
    <div className="bg-gray-800 border border-gray-700 p-4 rounded-lg mt-4 text-white">
      <h3 className="text-xl font-bold mb-3 text-blue-400 flex items-center">
        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        AI Explainability (SHAP)
      </h3>
      
      {/* Natural Language Explanation */}
      <div className="bg-gray-900 p-3 rounded border border-gray-600 mb-4">
        {explanationLines.map((line: string, idx: number) => (
          <p key={idx} className={`text-sm ${idx === 0 ? 'font-bold text-gray-200 mb-2' : 'text-gray-400 ml-2'}`}>
            {line}
          </p>
        ))}
      </div>

      {/* Feature Importance Bars */}
      <div>
        <h4 className="text-sm font-semibold text-gray-300 mb-2 uppercase tracking-wide">Key Risk Drivers</h4>
        <div className="space-y-2">
          {top_drivers && top_drivers.map((driver: any, idx: number) => {
            const isPositive = driver.value > 0;
            const widthPct = Math.min(Math.abs(driver.value) * 100 * 2, 100); // Scale for visibility
            
            return (
              <div key={idx} className="flex flex-col">
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>{driver.feature.replace(/_/g, ' ')}</span>
                  <span className={isPositive ? 'text-red-400' : 'text-green-400'}>
                    {isPositive ? '+' : ''}{driver.value.toFixed(3)}
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2 flex">
                  {/* Center origin layout for positive/negative impacts */}
                  <div className="w-1/2 flex justify-end">
                    {!isPositive && (
                      <div className="bg-green-500 h-2 rounded-l-full" style={{ width: `${widthPct}%` }}></div>
                    )}
                  </div>
                  <div className="w-1/2 flex justify-start border-l border-gray-500">
                    {isPositive && (
                      <div className="bg-red-500 h-2 rounded-r-full" style={{ width: `${widthPct}%` }}></div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ExplainabilityPanel;
