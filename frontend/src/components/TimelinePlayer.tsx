import React, { useState, useEffect } from 'react';

interface TimelinePlayerProps {
  timeseries: any[];
  onFrameChange: (frame: any) => void;
  lang?: string;
}

const translations: any = {
  en: { play: "Play", pause: "Pause", day: "Days Ago", event: "Event Phase" },
  hi: { play: "चलाएं", pause: "रोकें", day: "दिन पहले", event: "घटना चरण" },
  mr: { play: "सुरू करा", pause: "थांबवा", day: "दिवसांपूर्वी", event: "घटनेचा टप्पा" }
};

const TimelinePlayer: React.FC<TimelinePlayerProps> = ({ timeseries, onFrameChange, lang = 'en' }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const t = translations[lang] || translations.en;

  useEffect(() => {
    let interval: any;

    if (isPlaying && timeseries.length > 0) {
      interval = setInterval(() => {
        setCurrentIndex((prev) => {
          const next = prev + 1;
          if (next >= timeseries.length) {
            setIsPlaying(false);
            return prev;
          }
          return next;
        });
      }, 1000); // 1 second per frame
    }
    return () => clearInterval(interval);
  }, [isPlaying, timeseries]);

  useEffect(() => {
    if (timeseries.length > 0) {
      onFrameChange(timeseries[currentIndex]);
    }
  }, [currentIndex, timeseries, onFrameChange]);

  if (!timeseries || timeseries.length === 0) return null;

  const currentFrame = timeseries[currentIndex];

  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-700 mt-4">
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className={`px-4 py-2 rounded-md font-bold text-white transition ${
            isPlaying ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-500 hover:bg-blue-600'
          }`}
        >
          {isPlaying ? t.pause : t.play}
        </button>
        
        <div className="flex-1 mx-4">
          <input
            type="range"
            min="0"
            max={timeseries.length - 1}
            value={currentIndex}
            onChange={(e) => setCurrentIndex(Number(e.target.value))}
            className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer"
          />
        </div>
        
        <div className="text-right text-gray-300">
          <div className="font-bold">{t.day}: {currentFrame.days_ago}</div>
        </div>
      </div>
      
      <div className="grid grid-cols-4 gap-2 text-sm text-center">
        <div className="bg-gray-700 rounded p-2">
          <span className="text-gray-400 block">NDWI (Water)</span>
          <span className="font-bold text-blue-400">{currentFrame.ndwi.toFixed(3)}</span>
        </div>
        <div className="bg-gray-700 rounded p-2">
          <span className="text-gray-400 block">NDVI (Veg)</span>
          <span className="font-bold text-green-400">{currentFrame.ndvi.toFixed(3)}</span>
        </div>
        <div className="bg-gray-700 rounded p-2">
          <span className="text-gray-400 block">SAR (Radar)</span>
          <span className="font-bold text-purple-400">{currentFrame.sar_vv_db.toFixed(1)} dB</span>
        </div>
        <div className="bg-gray-700 rounded p-2">
          <span className="text-gray-400 block">Soil Moisture</span>
          <span className="font-bold text-yellow-400">{currentFrame.soil_moisture}%</span>
        </div>
      </div>
    </div>
  );
};

export default TimelinePlayer;
