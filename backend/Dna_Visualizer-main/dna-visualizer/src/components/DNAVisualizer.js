import { useState, useEffect } from 'react';

export default function DNAVisualizer() {
  const [rotationSpeed, setRotationSpeed] = useState(10);
  const [nucleotides, setNucleotides] = useState('ATCGATCGATCGATCGATCG');
  const [selectedComponent, setSelectedComponent] = useState(null);
  const [angle, setAngle] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  
  // Colors for nucleotides
  const colors = {
    'A': '#ff4d4d', // Adenine - red
    'T': '#4dff4d', // Thymine - green
    'C': '#4d4dff', // Cytosine - blue
    'G': '#ffff4d', // Guanine - yellow
  };
  
  const componentInfo = {
    'A': 'Adenine: A nitrogenous base that pairs with thymine in DNA.',
    'T': 'Thymine: A nitrogenous base that pairs with adenine in DNA.',
    'C': 'Cytosine: A nitrogenous base that pairs with guanine in DNA.',
    'G': 'Guanine: A nitrogenous base that pairs with cytosine in DNA.',
    'backbone': 'Phosphate-sugar backbone: The alternating phosphate and deoxyribose sugar groups that form the structural framework of the DNA strand.',
    'hydrogen': 'Hydrogen bonds: Weak bonds that hold complementary base pairs together.',
    'phosphate': 'Phosphate group: Contributes to the negative charge of DNA and forms part of the backbone.',
    'sugar': 'Deoxyribose sugar: The five-carbon sugar component of the DNA backbone.'
  };

  // Function to get complementary base
  const getComplementaryBase = (base) => {
    const pairs = { 'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C' };
    return pairs[base] || '';
  };

  // Update animation
  useEffect(() => {
    if (isPaused) return;
    
    const interval = setInterval(() => {
      setAngle(prev => (prev + rotationSpeed / 20) % 360);
    }, 50);
    
    return () => clearInterval(interval);
  }, [rotationSpeed, isPaused]);

  // Generate DNA structure
  const generateDNAStructure = () => {
    const basePairs = [];
    const helixRadius = 60;
    const verticalSpacing = 25;
    const helixHeight = nucleotides.length * verticalSpacing;
    
    for (let i = 0; i < nucleotides.length; i++) {
      const base = nucleotides[i];
      const complementaryBase = getComplementaryBase(base);
      const offsetAngle = angle + (i * 36); // 36 degrees per step for a complete turn every 10 nucleotides
      const radianAngle = offsetAngle * Math.PI / 180;
      
      // Calculate positions for base pairs
      const x1 = helixRadius * Math.cos(radianAngle);
      const z1 = helixRadius * Math.sin(radianAngle);
      const y1 = i * verticalSpacing - helixHeight / 2;
      
      const x2 = -x1;
      const z2 = -z1;
      const y2 = y1;
      
      // Adjust display based on z-position (depth)
      const opacity1 = ((Math.sin(radianAngle) + 1) / 2) * 0.5 + 0.5;
      const opacity2 = ((Math.sin(radianAngle + Math.PI) + 1) / 2) * 0.5 + 0.5;
      
      basePairs.push({
        id: i,
        base,
        complementaryBase,
        x1, y1, z1,
        x2, y2, z2,
        opacity1,
        opacity2,
        radianAngle
      });
    }
    
    return basePairs;
  };

  const handleInputChange = (e) => {
    // Filter input to only allow A, T, C, G
    const filtered = e.target.value.toUpperCase().replace(/[^ATCG]/g, '');
    setNucleotides(filtered);
  };

  const handleComponentClick = (component) => {
    setSelectedComponent(component);
  };
  
  const basePairs = generateDNAStructure();
  
  return (
    <div className="flex flex-col items-center p-4 gap-4 bg-gray-100 rounded-lg">
      <h2 className="text-2xl font-bold text-gray-800">DNA Visualization Tool</h2>
      
      {/* Controls */}
      <div className="flex flex-wrap gap-4 w-full max-w-3xl mb-4">
        <div className="bg-white p-4 rounded-lg shadow-md flex-1">
          <label className="block mb-2 font-medium">DNA Sequence:</label>
          <input
            type="text"
            value={nucleotides}
            onChange={handleInputChange}
            className="w-full p-2 border rounded"
            placeholder="Enter DNA sequence (A, T, C, G)"
          />
          <p className="text-sm text-gray-500 mt-1">Only A, T, C, G characters are allowed</p>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-md flex-1">
          <label className="block mb-2 font-medium">Rotation Speed:</label>
          <input
            type="range"
            min="0"
            max="50"
            value={rotationSpeed}
            onChange={(e) => setRotationSpeed(parseInt(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between mt-1">
            <span>Slow</span>
            <span>Fast</span>
          </div>
          <button
            onClick={() => setIsPaused(!isPaused)}
            className="mt-2 px-4 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            {isPaused ? 'Resume' : 'Pause'}
          </button>
        </div>
      </div>
      
      {/* Legend */}
      <div className="bg-white p-4 rounded-lg shadow-md w-full max-w-3xl mb-4">
        <h3 className="font-medium mb-2">Color Legend:</h3>
        <div className="flex flex-wrap gap-3">
          {Object.entries(colors).map(([base, color]) => (
            <div key={base} className="flex items-center">
              <div 
                style={{ backgroundColor: color }} 
                className="w-4 h-4 mr-1 rounded"
                onClick={() => handleComponentClick(base)}
              ></div>
              <span>{base}</span>
            </div>
          ))}
          <div className="flex items-center">
            <div className="w-4 h-4 mr-1 bg-gray-400 rounded" onClick={() => handleComponentClick('backbone')}></div>
            <span>Backbone</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 mr-1 bg-gray-800 rounded" onClick={() => handleComponentClick('hydrogen')}></div>
            <span>H-Bonds</span>
          </div>
        </div>
        <p className="text-sm text-gray-600 mt-2">Click on any component to learn more</p>
      </div>
      
      {/* Visualization */}
      <div className="bg-white p-4 rounded-lg shadow-md w-full max-w-3xl" style={{ height: '500px' }}>
        <svg width="100%" height="100%" viewBox="-150 -150 300 300">
          {/* Backbone Lines */}
          <path
            d={basePairs.map((pair, i) => 
              i === 0 
                ? `M${pair.x1},${pair.y1}` 
                : `L${pair.x1},${pair.y1}`
            ).join(' ')}
            fill="none"
            stroke="#888"
            strokeWidth="3"
            opacity="0.8"
            onClick={() => handleComponentClick('backbone')}
            className="cursor-pointer"
          />
          
          <path
            d={basePairs.map((pair, i) => 
              i === 0 
                ? `M${pair.x2},${pair.y2}` 
                : `L${pair.x2},${pair.y2}`
            ).join(' ')}
            fill="none"
            stroke="#888"
            strokeWidth="3"
            opacity="0.8"
            onClick={() => handleComponentClick('backbone')}
            className="cursor-pointer"
          />
          
          {/* Base pairs and hydrogen bonds */}
          {basePairs.map((pair) => (
            <g key={pair.id}>
              {/* Left nucleotide */}
              <circle
                cx={pair.x1}
                cy={pair.y1}
                r={8}
                fill={colors[pair.base] || '#888'}
                opacity={pair.opacity1}
                stroke="#333"
                strokeWidth="0.5"
                onClick={() => handleComponentClick(pair.base)}
                className="cursor-pointer"
              />
              
              {/* Right nucleotide */}
              <circle
                cx={pair.x2}
                cy={pair.y2}
                r={8}
                fill={colors[pair.complementaryBase] || '#888'}
                opacity={pair.opacity2}
                stroke="#333"
                strokeWidth="0.5"
                onClick={() => handleComponentClick(pair.complementaryBase)}
                className="cursor-pointer"
              />
              
              {/* Hydrogen bonds */}
              <line
                x1={pair.x1}
                y1={pair.y1}
                x2={pair.x2}
                y2={pair.y2}
                stroke="#000"
                strokeWidth="2"
                opacity={(pair.opacity1 + pair.opacity2) / 2}
                strokeDasharray="3,2"
                onClick={() => handleComponentClick('hydrogen')}
                className="cursor-pointer"
              />
              
              {/* Base labels */}
              <text
                x={pair.x1}
                y={pair.y1}
                textAnchor="middle"
                dy="0.3em"
                fontSize="9"
                fontWeight="bold"
                fill="#fff"
                opacity={pair.opacity1}
              >
                {pair.base}
              </text>
              
              <text
                x={pair.x2}
                y={pair.y2}
                textAnchor="middle"
                dy="0.3em"
                fontSize="9"
                fontWeight="bold"
                fill="#fff"
                opacity={pair.opacity2}
              >
                {pair.complementaryBase}
              </text>
            </g>
          ))}
        </svg>
      </div>
      
      {/* Information Panel */}
      {selectedComponent && (
        <div className="bg-white p-4 rounded-lg shadow-md w-full max-w-3xl mt-4">
          <h3 className="font-medium mb-2">Component Information:</h3>
          <p>{componentInfo[selectedComponent] || `${selectedComponent}: No information available.`}</p>
        </div>
      )}
    </div>
  );
}
