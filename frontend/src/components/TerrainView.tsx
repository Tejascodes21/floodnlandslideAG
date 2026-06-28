import React from 'react';

interface TerrainViewProps {
  data: {
    elevation: number;
    slope: number;
    aspect: number;
    terrain_roughness: number;
    terrain_class: string;
  };
  lang?: string;
}

const translations: any = {
  en: { elev: "Elevation", slope: "Slope", aspect: "Aspect", rough: "Roughness", cls: "Class" },
  hi: { elev: "ऊंचाई", slope: "ढलान", aspect: "दिशा", rough: "खुरदरापन", cls: "वर्ग" },
  mr: { elev: "उंची", slope: "उतार", aspect: "दिशा", rough: "खडबडीतपणा", cls: "वर्ग" }
};

const TerrainView: React.FC<TerrainViewProps> = ({ data, lang = 'en' }) => {
  if (!data) return null;
  const t = translations[lang] || translations.en;

  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-700 mt-4">
      <h3 className="text-xl font-semibold mb-3 text-white border-b border-gray-600 pb-2">Terrain Profile</h3>
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-gray-700 p-3 rounded">
          <p className="text-gray-400 text-sm">{t.elev}</p>
          <p className="text-xl font-bold text-white">{data.elevation.toFixed(1)} <span className="text-sm font-normal">m ASL</span></p>
        </div>
        <div className="bg-gray-700 p-3 rounded">
          <p className="text-gray-400 text-sm">{t.slope}</p>
          <p className="text-xl font-bold text-orange-400">{data.slope.toFixed(1)}°</p>
        </div>
        <div className="bg-gray-700 p-3 rounded">
          <p className="text-gray-400 text-sm">{t.rough}</p>
          <p className="text-lg font-semibold text-gray-200">{data.terrain_roughness.toFixed(2)}</p>
        </div>
        <div className="bg-gray-700 p-3 rounded">
          <p className="text-gray-400 text-sm">{t.cls}</p>
          <p className="text-md font-semibold text-blue-300 truncate" title={data.terrain_class}>{data.terrain_class}</p>
        </div>
      </div>
    </div>
  );
};

export default TerrainView;
