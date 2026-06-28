import React, { useState, useEffect } from 'react';
import { BookOpen, CheckSquare, HeartHandshake, ShieldAlert, Phone, HelpCircle, FileText, AlertTriangle, HelpCircle as HelpIcon } from 'lucide-react';

interface DisasterGuidelinesProps {
  lang: 'en' | 'hi' | 'mr';
}

const guidelinesTranslations = {
  en: {
    title: "EOC Emergency response Protocols Deck",
    sub: "Standard Operating Procedures (SOPs), warnings dictionaries, and safety gear checklists",
    tab_warnings: "EOC Warning Code Hierarchy",
    tab_kits: "Emergency Survival kit Checklist",
    tab_protocols: "Standard disaster Protocols",
    warning_red: "Red alert (Extreme)",
    warning_red_desc: "Precipitation exceeding 115mm/24h or flood depth > 4m. Evacuate immediately. Pre-position volunteer boat vectors.",
    warning_orange: "Orange alert (Severe)",
    warning_orange_desc: "Precipitation 64-115mm/24h or soil moisture > 80%. Prepare evacuations, monitor hillside channels.",
    warning_yellow: "Yellow alert (Moderate)",
    warning_yellow_desc: "Precipitation 15-64mm/24h. Monitor water level gauges and meteorological advisories closely.",
    kit_desc: "EOC advisory: Maintain this emergency safety gear in a waterproof, accessible backpack.",
    kit_item_1: "Drinking Water (3 Litres per person/day)",
    kit_item_2: "Non-perishable dry foodstuffs (3-day supply)",
    kit_item_3: "High-power Flashlight + extra batteries",
    kit_item_4: "Emergency Paramedic First Aid Kit",
    kit_item_5: "Portable AM/FM Battery Radio",
    kit_item_6: "Whistle (to broadcast distress acoustics)",
    kit_item_7: "Laminated copies of government ID & maps",
    kit_item_8: "Powerbank for mobile device survival",
    protocol_flood: "Flash Flood Action SOPs",
    protocol_flood_steps: [
      "Immediately disconnect main electric circuits and gas pipeline inlets.",
      "Proceed immediately to designated high-elevation camps (>150m DEM).",
      "Do NOT attempt to walk or drive through flowing water currents.",
      "Geotag report landmarks or trigger EOC SOS signals for boat dispatches."
    ],
    protocol_landslide: "Hillside Landslide Action SOPs",
    protocol_landslide_steps: [
      "Evacuate steep terrain corridors if soil moisture indices exceed 80%.",
      "If indoors, retreat immediately to upper floors or soundly-built sectors.",
      "Stay highly alert for rumbling acoustics, cracking trees, or rolling debris.",
      "Avoid low-lying stream beds and run-off drainage channels."
    ],
    contacts_title: "EOC Regional Distress Directory",
    contacts_sub: "Emergency control coordinate lines"
  },
  hi: {
    title: "ईओसी आपातकालीन प्रतिक्रिया प्रोटोकॉल डेक",
    sub: "मानक संचालन प्रक्रियाएं (SOPs), चेतावनी निर्देशिका और आपातकालीन किट चेकलिस्ट",
    tab_warnings: "ईओसी चेतावनी कोड पदानुक्रम",
    tab_kits: "आपातकालीन जीवन रक्षा किट चेकलिस्ट",
    tab_protocols: "मानक आपदा प्रोटोकॉल",
    warning_red: "रेड अलर्ट (अत्यधिक)",
    warning_red_desc: "वर्षा ११५ मिमी/२४ घंटे से अधिक या बाढ़ की गहराई > ४ मीटर। तुरंत खाली करें। बचाव नौकाओं को तैनात करें।",
    warning_orange: "ऑरेंज अलर्ट (गंभीर)",
    warning_orange_desc: "वर्षा ६४-११५ मिमी/२४ घंटे या मिट्टी की नमी > ८०%। निकासी की तैयारी करें, पहाड़ी रास्तों की निगरानी करें।",
    warning_yellow: "येलो अलर्ट (सामान्य)",
    warning_yellow_desc: "वर्षा १५-६४ मिमी/२४ घंटे। जल स्तर गेज और मौसम विभाग की सलाह की बारीकी से निगरानी करें।",
    kit_desc: "ईओसी सलाह: इस आपातकालीन सुरक्षा गियर को जलरोधक, सुलभ बैकपैक में रखें।",
    kit_item_1: "पीने का पानी (३ लीटर प्रति व्यक्ति/दिन)",
    kit_item_2: "जल्दी खराब न होने वाला सूखा भोजन (३ दिनों का स्टॉक)",
    kit_item_3: "हाई-पावर टॉर्च + अतिरिक्त बैटरी",
    kit_item_4: "आपातकालीन प्राथमिक चिकित्सा किट (First Aid)",
    kit_item_5: "पोर्टेबल बैटरी चालित रेडियो",
    kit_item_6: "सीटी (ध्वनि संकट संकेत प्रसारित करने के लिए)",
    kit_item_7: "पहचान पत्र और सरकारी मानचित्रों की प्रतियां",
    kit_item_8: "मोबाइल डिवाइस के लिए पावरबैंक",
    protocol_flood: "बाढ़ सुरक्षा नियम (SOPs)",
    protocol_flood_steps: [
      "तुरंत मुख्य विद्युत सर्किट और गैस पाइपलाइन इनलेट को बंद कर दें।",
      "निर्दिष्ट उच्च ऊंचाई वाले शिविरों (>१५० मीटर ऊंचाई) में तुरंत जाएं।",
      "बहते पानी की धाराओं में चलने या वाहन चलाने का प्रयास न करें।",
      "निकासी के लिए भू-स्थानिक रिपोर्ट दर्ज करें या आपातकालीन एसओएस भेजें।"
    ],
    protocol_landslide: "भूस्खलन सुरक्षा नियम (SOPs)",
    protocol_landslide_steps: [
      "यदि मिट्टी की नमी का स्तर ८०% से अधिक हो तो पहाड़ी रास्तों को खाली कर दें।",
      "यदि घर के अंदर हैं, तो तुरंत ऊपरी मंजिलों या मजबूत कमरे में जाएं।",
      "गड़गड़ाहट की आवाज़, पेड़ों के टूटने या मलबे के गिरने पर सतर्क रहें।",
      "निचली नदी घाटियों और ढलान वाले जल निकासी मार्गों से दूर रहें।"
    ],
    contacts_title: "ईओसी क्षेत्रीय आपातकालीन संपर्क",
    contacts_sub: "आपातकालीन नियंत्रण कक्ष हॉटलाइन नंबर"
  },
  mr: {
    title: "ईओसी आपत्ती आपत्कालीन मार्गदर्शक तत्त्वे",
    sub: "मानक कार्यपद्धती (SOPs), इशारा फलक आणि आपत्कालीन साहित्य चेकलिस्ट",
    tab_warnings: "ईओसी आपत्ती इशारा स्तर",
    tab_kits: "आपत्कालीन जीवनरक्षक किट चेकलिस्ट",
    tab_protocols: "मानक आपत्ती नियमावली",
    warning_red: "लाल इशारा (अति तीव्र धोका)",
    warning_red_desc: "मुसळधार पाऊस > ११५ मिमी/२४ तास किंवा पूर पातळी > ४ मीटर. त्वरित स्थलांतर करा. मदत नौका तैनात करा.",
    warning_orange: "नारिंगी इशारा (तीव्र धोका)",
    warning_orange_desc: "पाऊस ६४-११५ मिमी/२४ तास किंवा माती आर्द्रता > ८०%. स्थलांतराची तयारी करा, डोंगरउतारांवर लक्ष ठेवा.",
    warning_yellow: "पिवळा इशारा (मध्यम धोका)",
    warning_yellow_desc: "पाऊस १५-६४ मिमी/२४ तास. नदीच्या पाणी पातळीवर आणि हवामान अंदाजावर लक्ष ठेवा.",
    kit_desc: "ईओसी सूचना: आपत्कालीन वापराचे साहित्य वॉटरप्रूफ आणि जवळच्या बॅगेत तयार ठेवावे.",
    kit_item_1: "पिण्याचे पाणी (३ लिटर प्रति व्यक्ती/दिवस)",
    kit_item_2: "३ दिवस टिकणारे सुके अन्नपदार्थ",
    kit_item_3: "टॉर्च आणि अतिरिक्त बॅटरी",
    kit_item_4: "औषधोपचार आणि प्रथमोपचार पेटी (First Aid)",
    kit_item_5: "पोर्टेबल रेडिओ (FM/AM)",
    kit_item_6: "शिट्टी (मदतीचा आवाज देण्यासाठी)",
    kit_item_7: "ओळखपत्र आणि महत्त्वाच्या नकाशांच्या प्रती",
    kit_item_8: "मोबाईल चार्जिंगसाठी पॉवर बँक",
    protocol_flood: "महापूर आपत्कालीन नियमावली",
    protocol_flood_steps: [
      "घरातील वीज पुरवठा आणि गॅस कनेक्शन तातडीने बंद करा.",
      "उंचीवरील निवारा केंद्रात (>१५० मीटर उंची) त्वरित स्थलांतर करा.",
      "पुराच्या पाण्यातून चालण्याचा किंवा गाडी चालवण्याचा प्रयत्न करू नका.",
      "नकाशावर लोकेशन नोंदवा किंवा ईओसी मदत संदेश (SOS) पाठवा."
    ],
    protocol_landslide: "दरड कोसळणे आपत्कालीन नियमावली",
    protocol_landslide_steps: [
      "मातीची आर्द्रता ८०% पेक्षा जास्त झाल्यास डोंगरउतारावरील घरे तातडीने खाली करा.",
      "घरात अडकल्यास तात्काळ वरील मजल्यावर किंवा सुरक्षित ठिकाणी जा.",
      "दगडांचा आवाज किंवा दरड कोसळण्याच्या हालचालींवर बारीक लक्ष ठेवा.",
      "पाण्याचे नैसर्गिक प्रवाह आणि डोंगर पायथ्याकडील भाग टाळा."
    ],
    contacts_title: "आपत्कालीन नियंत्रण कक्ष संपर्क",
    contacts_sub: "तातडीच्या मदतीसाठी नियंत्रण कक्ष नंबर"
  }
};

export default function DisasterGuidelines({ lang }: DisasterGuidelinesProps) {
  const t = guidelinesTranslations[lang];

  const [activeSubTab, setActiveSubTab] = useState<'warnings' | 'kits' | 'protocols'>('warnings');
  
  // Checklist state loaded from LocalStorage
  const [checklist, setChecklist] = useState<Record<string, boolean>>(() => {
    try {
      const saved = localStorage.getItem('eoc_survival_checklist');
      return saved ? JSON.parse(saved) : {
        water: false,
        food: false,
        flashlight: false,
        firstaid: false,
        radio: false,
        whistle: false,
        iddocs: false,
        powerbank: false
      };
    } catch {
      return {
        water: false,
        food: false,
        flashlight: false,
        firstaid: false,
        radio: false,
        whistle: false,
        iddocs: false,
        powerbank: false
      };
    }
  });

  useEffect(() => {
    localStorage.setItem('eoc_survival_checklist', JSON.stringify(checklist));
  }, [checklist]);

  const toggleCheck = (key: string) => {
    setChecklist(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const getCompletedCount = () => {
    return Object.values(checklist).filter(Boolean).length;
  };

  return (
    <div className="space-y-6">
      
      {/* Header Info Panel */}
      <div className="glass-panel p-6 rounded-2xl border border-borderDim flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-24 h-full satellite-scanner pointer-events-none"></div>
        <div>
          <h2 className="text-lg font-bold text-textMain flex items-center gap-2">
            <BookOpen className="text-blue-500 w-5 h-5 shrink-0" />
            {t.title}
          </h2>
          <p className="text-xs text-textMuted mt-1">{t.sub}</p>
        </div>
      </div>

      {/* Internal Navigation Tabs */}
      <div className="flex border-b border-borderDim text-xs font-bold shrink-0">
        <button
          onClick={() => setActiveSubTab('warnings')}
          className={`px-6 py-3 border-b-2 transition-all ${
            activeSubTab === 'warnings' 
              ? 'border-blue-500 text-blue-400 font-extrabold' 
              : 'border-transparent text-textMuted hover:text-textMain'
          }`}
        >
          {t.tab_warnings}
        </button>
        <button
          onClick={() => setActiveSubTab('kits')}
          className={`px-6 py-3 border-b-2 transition-all ${
            activeSubTab === 'kits' 
              ? 'border-blue-500 text-blue-400 font-extrabold' 
              : 'border-transparent text-textMuted hover:text-textMain'
          }`}
        >
          {t.tab_kits}
        </button>
        <button
          onClick={() => setActiveSubTab('protocols')}
          className={`px-6 py-3 border-b-2 transition-all ${
            activeSubTab === 'protocols' 
              ? 'border-blue-500 text-blue-400 font-extrabold' 
              : 'border-transparent text-textMuted hover:text-textMain'
          }`}
        >
          {t.tab_protocols}
        </button>
      </div>

      {/* Tab Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Side Content Deck */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Tab 1: Warning Levels */}
          {activeSubTab === 'warnings' && (
            <div className="space-y-4">
              
              {/* Red Warning */}
              <div className="glass-panel p-5 rounded-2xl border-l-4 border-l-red-500 border-borderDim flex gap-4">
                <ShieldAlert className="text-red-500 w-8 h-8 shrink-0 pulse-threat" />
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-red-400 uppercase tracking-wide">{t.warning_red}</h4>
                  <p className="text-xs text-textMuted leading-relaxed font-semibold">
                    {t.warning_red_desc}
                  </p>
                </div>
              </div>

              {/* Orange Warning */}
              <div className="glass-panel p-5 rounded-2xl border-l-4 border-l-orange-500 border-borderDim flex gap-4">
                <AlertTriangle className="text-orange-500 w-8 h-8 shrink-0 animate-pulse" />
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-orange-400 uppercase tracking-wide">{t.warning_orange}</h4>
                  <p className="text-xs text-textMuted leading-relaxed font-semibold">
                    {t.warning_orange_desc}
                  </p>
                </div>
              </div>

              {/* Yellow Warning */}
              <div className="glass-panel p-5 rounded-2xl border-l-4 border-l-amber-500 border-borderDim flex gap-4">
                <AlertTriangle className="text-amber-500 w-8 h-8 shrink-0" />
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-amber-400 uppercase tracking-wide">{t.warning_yellow}</h4>
                  <p className="text-xs text-textMuted leading-relaxed font-semibold">
                    {t.warning_yellow_desc}
                  </p>
                </div>
              </div>

            </div>
          )}

          {/* Tab 2: Survival Kit Checklists */}
          {activeSubTab === 'kits' && (
            <div className="glass-panel p-5 rounded-2xl border border-borderDim space-y-4">
              <div className="border-b border-slate-900 pb-3 flex justify-between items-center">
                <div>
                  <h3 className="text-xs font-bold text-textMain uppercase tracking-wide">Emergency Back-Pack Gear</h3>
                  <p className="text-[10px] text-textMuted mt-0.5">{t.kit_desc}</p>
                </div>
                <span className="text-[10px] font-black text-blue-400 bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/30">
                  {getCompletedCount()} / 8 Ready
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-semibold">
                
                {/* 1 */}
                <label className="flex items-center gap-3 p-3 bg-slate-950/40 hover:bg-slate-950 border border-borderDim/50 hover:border-blue-500/30 rounded-xl cursor-pointer transition-all">
                  <input
                    type="checkbox" checked={checklist.water} onChange={() => toggleCheck('water')}
                    className="w-4 h-4 accent-blue-500 rounded"
                  />
                  <span className={checklist.water ? 'line-through text-slate-500' : 'text-textMain'}>{t.kit_item_1}</span>
                </label>

                {/* 2 */}
                <label className="flex items-center gap-3 p-3 bg-slate-950/40 hover:bg-slate-950 border border-borderDim/50 hover:border-blue-500/30 rounded-xl cursor-pointer transition-all">
                  <input
                    type="checkbox" checked={checklist.food} onChange={() => toggleCheck('food')}
                    className="w-4 h-4 accent-blue-500 rounded"
                  />
                  <span className={checklist.food ? 'line-through text-slate-500' : 'text-textMain'}>{t.kit_item_2}</span>
                </label>

                {/* 3 */}
                <label className="flex items-center gap-3 p-3 bg-slate-950/40 hover:bg-slate-950 border border-borderDim/50 hover:border-blue-500/30 rounded-xl cursor-pointer transition-all">
                  <input
                    type="checkbox" checked={checklist.flashlight} onChange={() => toggleCheck('flashlight')}
                    className="w-4 h-4 accent-blue-500 rounded"
                  />
                  <span className={checklist.flashlight ? 'line-through text-slate-500' : 'text-textMain'}>{t.kit_item_3}</span>
                </label>

                {/* 4 */}
                <label className="flex items-center gap-3 p-3 bg-slate-950/40 hover:bg-slate-950 border border-borderDim/50 hover:border-blue-500/30 rounded-xl cursor-pointer transition-all">
                  <input
                    type="checkbox" checked={checklist.firstaid} onChange={() => toggleCheck('firstaid')}
                    className="w-4 h-4 accent-blue-500 rounded"
                  />
                  <span className={checklist.firstaid ? 'line-through text-slate-500' : 'text-textMain'}>{t.kit_item_4}</span>
                </label>

                {/* 5 */}
                <label className="flex items-center gap-3 p-3 bg-slate-950/40 hover:bg-slate-950 border border-borderDim/50 hover:border-blue-500/30 rounded-xl cursor-pointer transition-all">
                  <input
                    type="checkbox" checked={checklist.radio} onChange={() => toggleCheck('radio')}
                    className="w-4 h-4 accent-blue-500 rounded"
                  />
                  <span className={checklist.radio ? 'line-through text-slate-500' : 'text-textMain'}>{t.kit_item_5}</span>
                </label>

                {/* 6 */}
                <label className="flex items-center gap-3 p-3 bg-slate-950/40 hover:bg-slate-950 border border-borderDim/50 hover:border-blue-500/30 rounded-xl cursor-pointer transition-all">
                  <input
                    type="checkbox" checked={checklist.whistle} onChange={() => toggleCheck('whistle')}
                    className="w-4 h-4 accent-blue-500 rounded"
                  />
                  <span className={checklist.whistle ? 'line-through text-slate-500' : 'text-textMain'}>{t.kit_item_6}</span>
                </label>

                {/* 7 */}
                <label className="flex items-center gap-3 p-3 bg-slate-950/40 hover:bg-slate-950 border border-borderDim/50 hover:border-blue-500/30 rounded-xl cursor-pointer transition-all">
                  <input
                    type="checkbox" checked={checklist.iddocs} onChange={() => toggleCheck('iddocs')}
                    className="w-4 h-4 accent-blue-500 rounded"
                  />
                  <span className={checklist.iddocs ? 'line-through text-slate-500' : 'text-textMain'}>{t.kit_item_7}</span>
                </label>

                {/* 8 */}
                <label className="flex items-center gap-3 p-3 bg-slate-950/40 hover:bg-slate-950 border border-borderDim/50 hover:border-blue-500/30 rounded-xl cursor-pointer transition-all">
                  <input
                    type="checkbox" checked={checklist.powerbank} onChange={() => toggleCheck('powerbank')}
                    className="w-4 h-4 accent-blue-500 rounded"
                  />
                  <span className={checklist.powerbank ? 'line-through text-slate-500' : 'text-textMain'}>{t.kit_item_8}</span>
                </label>

              </div>
            </div>
          )}

          {/* Tab 3: Disaster SOP Protocols */}
          {activeSubTab === 'protocols' && (
            <div className="space-y-6">
              
              {/* Flood SOP */}
              <div className="glass-panel p-5 rounded-2xl border border-borderDim space-y-3">
                <h4 className="text-xs font-bold text-blue-400 uppercase tracking-wide flex items-center gap-1.5">
                  <FileText className="w-4 h-4" />
                  {t.protocol_flood}
                </h4>
                <ul className="space-y-2 text-xs text-textMuted leading-relaxed font-semibold pl-2">
                  {t.protocol_flood_steps.map((step, idx) => (
                    <li key={idx} className="flex gap-2 items-start">
                      <span className="text-blue-500 font-black">{idx + 1}.</span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Landslide SOP */}
              <div className="glass-panel p-5 rounded-2xl border border-borderDim space-y-3">
                <h4 className="text-xs font-bold text-orange-400 uppercase tracking-wide flex items-center gap-1.5">
                  <FileText className="w-4 h-4" />
                  {t.protocol_landslide}
                </h4>
                <ul className="space-y-2 text-xs text-textMuted leading-relaxed font-semibold pl-2">
                  {t.protocol_landslide_steps.map((step, idx) => (
                    <li key={idx} className="flex gap-2 items-start">
                      <span className="text-orange-500 font-black">{idx + 1}.</span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ul>
              </div>

            </div>
          )}

        </div>

        {/* Right Side Contact Directory Card */}
        <div className="lg:col-span-1 glass-panel p-5 rounded-2xl border border-borderDim space-y-4 h-fit">
          <h3 className="text-xs font-bold text-textMain border-b border-slate-900 pb-3 uppercase tracking-wide flex items-center gap-1.5">
            <Phone className="w-4 h-4 text-blue-500" />
            {t.contacts_title}
          </h3>
          
          <div className="space-y-3.5 text-xs font-semibold">
            {/* contact 1 */}
            <div className="p-3 bg-slate-950/60 border border-slate-900 rounded-xl space-y-1">
              <span className="text-slate-500 text-[10px] uppercase font-bold block">EOC Central Control</span>
              <span className="text-textMain block font-bold">Mumbai EOC Hotline</span>
              <span className="text-blue-400 font-mono">+91 22 2262 0380</span>
            </div>
            
            {/* contact 2 */}
            <div className="p-3 bg-slate-950/60 border border-slate-900 rounded-xl space-y-1">
              <span className="text-slate-500 text-[10px] uppercase font-bold block">Disaster Management Bureau</span>
              <span className="text-textMain block font-bold">National Helpline</span>
              <span className="text-blue-400 font-mono">1078 (toll-free)</span>
            </div>

            {/* contact 3 */}
            <div className="p-3 bg-slate-950/60 border border-slate-900 rounded-xl space-y-1">
              <span className="text-slate-500 text-[10px] uppercase font-bold block">National Responders Command</span>
              <span className="text-textMain block font-bold">NDRF Control Deck</span>
              <span className="text-blue-400 font-mono">+91 97110 77372</span>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
