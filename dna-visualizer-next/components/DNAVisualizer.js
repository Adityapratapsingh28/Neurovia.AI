"use client";
import { useState, useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

export default function DNAVisualizer3D() {
  const [rotationSpeed, setRotationSpeed] = useState(10);
  const [nucleotides, setNucleotides] = useState('ATCGATCGATCGATCGATCG');
  const [selectedComponent, setSelectedComponent] = useState(null);
  const [isPaused, setIsPaused] = useState(false);
  const [viewMode, setViewMode] = useState('3d'); // '3d' or '2d'
  const [showLabels, setShowLabels] = useState(true);
  
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef = useRef(null);
  const controlsRef = useRef(null);
  const animationRef = useRef(null);
  const objectsRef = useRef([]);
  
  // Colors for nucleotides
  const colors = {
    'A': 0xff4d4d, // Adenine - red
    'T': 0x4dff4d, // Thymine - green
    'C': 0x4d4dff, // Cytosine - blue
    'G': 0xffff4d, // Guanine - yellow
    'backbone': 0x888888,
    'hydrogen': 0x333333,
    'phosphate': 0x6666ff,
    'sugar': 0xdddddd
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

  // Initialize Three.js
  useEffect(() => {
    if (!mountRef.current) return;
    
    // Setup scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf5f5f5);
    sceneRef.current = scene;
    
    // Setup camera
    const camera = new THREE.PerspectiveCamera(
      75, 
      mountRef.current.clientWidth / mountRef.current.clientHeight, 
      0.1, 
      1000
    );
    camera.position.z = 150;
    cameraRef.current = camera;
    
    // Setup renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;
    
    // Add lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(0, 200, 100);
    scene.add(directionalLight);
    
    // Add controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controlsRef.current = controls;
    
    // Add helper grid
    const gridHelper = new THREE.GridHelper(200, 20, 0x555555, 0x333333);
    gridHelper.position.y = -50;
    scene.add(gridHelper);
    
    // Initial render
    createDNAModel();
    
    // Animation loop
    const animate = () => {
      animationRef.current = requestAnimationFrame(animate);
      
      if (!isPaused && viewMode === '3d') {
        // Rotate the entire DNA model
        if (objectsRef.current.dnaGroup) {
          objectsRef.current.dnaGroup.rotation.y += rotationSpeed * 0.001;
        }
      }
      
      controls.update();
      renderer.render(scene, camera);
    };
    
    animate();
    
    // Handle resize
    const handleResize = () => {
      if (!mountRef.current) return;
      
      const width = mountRef.current.clientWidth;
      const height = mountRef.current.clientHeight;
      
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    
    window.addEventListener('resize', handleResize);
    
    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (rendererRef.current && mountRef.current) {
        mountRef.current.removeChild(rendererRef.current.domElement);
      }
      
      // Dispose all geometries and materials
      if (sceneRef.current) {
        sceneRef.current.traverse((object) => {
          if (object.geometry) object.geometry.dispose();
          if (object.material) {
            if (Array.isArray(object.material)) {
              object.material.forEach(material => material.dispose());
            } else {
              object.material.dispose();
            }
          }
        });
      }
    };
  }, []);
  
  // Create or update DNA model when nucleotides change
  useEffect(() => {
    createDNAModel();
  }, [nucleotides, viewMode, showLabels]);
  
  // Update rotation speed
  useEffect(() => {
    // We don't need to do anything here, as rotation speed is used directly in the animation loop
  }, [rotationSpeed]);
  
  // Handle pause state
  useEffect(() => {
    // Animation loop already checks isPaused
  }, [isPaused]);
  
  // Function to clear the current DNA model
  const clearDNAModel = () => {
    if (sceneRef.current && objectsRef.current.dnaGroup) {
      sceneRef.current.remove(objectsRef.current.dnaGroup);
      
      // Dispose materials and geometries
      objectsRef.current.dnaGroup.traverse((object) => {
        if (object.geometry) object.geometry.dispose();
        if (object.material) {
          if (Array.isArray(object.material)) {
            object.material.forEach(material => material.dispose());
          } else {
            object.material.dispose();
          }
        }
      });
    }
  };
  
  // Function to create DNA model
  const createDNAModel = () => {
    if (!sceneRef.current) return;
    
    // Clear previous model
    clearDNAModel();
    
    // Create a new group for the DNA
    const dnaGroup = new THREE.Group();
    objectsRef.current.dnaGroup = dnaGroup;
    
    // Parameters
    const helixRadius = 20;
    const verticalSpacing = 5;
    const helixHeight = nucleotides.length * verticalSpacing;
    const torusRadius = 2;
    const cylinderRadius = 0.6;
    
    // Reusable geometries
    const nucleotideGeometry = new THREE.SphereGeometry(3, 32, 16);
    const phosphateGeometry = new THREE.SphereGeometry(1.5, 16, 8);
    const sugarGeometry = new THREE.SphereGeometry(1.2, 16, 8);
    
    // Backbone splines
    const backbone1Points = [];
    const backbone2Points = [];
    
    // Create base pairs
    for (let i = 0; i < nucleotides.length; i++) {
      const base = nucleotides[i];
      const complementaryBase = getComplementaryBase(base);
      const angle = i * 36 * (Math.PI / 180); // 36 degrees per step
      
      // Calculate positions
      const x1 = helixRadius * Math.cos(angle);
      const z1 = helixRadius * Math.sin(angle);
      const y1 = i * verticalSpacing - helixHeight / 2;
      
      const x2 = -x1;
      const z2 = -z1;
      const y2 = y1;
      
      // Add points to backbone splines
      backbone1Points.push(new THREE.Vector3(x1, y1, z1));
      backbone2Points.push(new THREE.Vector3(x2, y2, z2));
      
      // Create nucleotides
      const nucleotide1Material = new THREE.MeshPhongMaterial({ 
        color: colors[base],
        shininess: 80
      });
      const nucleotide1 = new THREE.Mesh(nucleotideGeometry, nucleotide1Material);
      nucleotide1.position.set(x1, y1, z1);
      nucleotide1.userData = { 
        type: 'nucleotide', 
        base: base,
        info: componentInfo[base]
      };
      dnaGroup.add(nucleotide1);
      
      const nucleotide2Material = new THREE.MeshPhongMaterial({ 
        color: colors[complementaryBase],
        shininess: 80
      });
      const nucleotide2 = new THREE.Mesh(nucleotideGeometry, nucleotide2Material);
      nucleotide2.position.set(x2, y2, z2);
      nucleotide2.userData = { 
        type: 'nucleotide', 
        base: complementaryBase,
        info: componentInfo[complementaryBase]
      };
      dnaGroup.add(nucleotide2);
      
      // Create hydrogen bonds
      const bondDirection = new THREE.Vector3(x2 - x1, y2 - y1, z2 - z1);
      const bondLength = bondDirection.length();
      bondDirection.normalize();
      
      const hydrogenGeometry = new THREE.CylinderGeometry(
        cylinderRadius, cylinderRadius, bondLength, 8, 1
      );
      const hydrogenMaterial = new THREE.MeshBasicMaterial({ 
        color: colors.hydrogen,
        transparent: true,
        opacity: 0.7
      });
      
      const hydrogen = new THREE.Mesh(hydrogenGeometry, hydrogenMaterial);
      
      // Position the hydrogen bond
      hydrogen.position.set(
        (x1 + x2) / 2,
        (y1 + y2) / 2,
        (z1 + z2) / 2
      );
      
      // Orient the hydrogen bond
      hydrogen.lookAt(x2, y2, z2);
      hydrogen.rotateX(Math.PI / 2);
      
      hydrogen.userData = { 
        type: 'hydrogen',
        info: componentInfo.hydrogen
      };
      
      dnaGroup.add(hydrogen);
      
      // Add phosphate and sugar groups to backbone
      if (viewMode === '3d') {
        // Phosphate group for strand 1
        const phosphate1 = new THREE.Mesh(
          phosphateGeometry,
          new THREE.MeshPhongMaterial({ color: colors.phosphate })
        );
        phosphate1.position.set(
          x1 * 1.2, 
          y1 + verticalSpacing/2, 
          z1 * 1.2
        );
        phosphate1.userData = { 
          type: 'phosphate',
          info: componentInfo.phosphate
        };
        dnaGroup.add(phosphate1);
        
        // Sugar group for strand 1
        const sugar1 = new THREE.Mesh(
          sugarGeometry,
          new THREE.MeshPhongMaterial({ color: colors.sugar })
        );
        sugar1.position.set(
          x1 * 1.1, 
          y1, 
          z1 * 1.1
        );
        sugar1.userData = { 
          type: 'sugar',
          info: componentInfo.sugar
        };
        dnaGroup.add(sugar1);
        
        // Phosphate group for strand 2
        const phosphate2 = new THREE.Mesh(
          phosphateGeometry,
          new THREE.MeshPhongMaterial({ color: colors.phosphate })
        );
        phosphate2.position.set(
          x2 * 1.2, 
          y2 + verticalSpacing/2, 
          z2 * 1.2
        );
        phosphate2.userData = { 
          type: 'phosphate',
          info: componentInfo.phosphate
        };
        dnaGroup.add(phosphate2);
        
        // Sugar group for strand 2
        const sugar2 = new THREE.Mesh(
          sugarGeometry,
          new THREE.MeshPhongMaterial({ color: colors.sugar })
        );
        sugar2.position.set(
          x2 * 1.1, 
          y2, 
          z2 * 1.1
        );
        sugar2.userData = { 
          type: 'sugar',
          info: componentInfo.sugar
        };
        dnaGroup.add(sugar2);
      }
      
      // Add labels if enabled
      if (showLabels) {
        const createTextSprite = (text, position, color) => {
          const canvas = document.createElement('canvas');
          const context = canvas.getContext('2d');
          canvas.width = 64;
          canvas.height = 64;
          
          context.fillStyle = '#ffffff';
          context.fillRect(0, 0, canvas.width, canvas.height);
          
          context.font = '48px Arial';
          context.fillStyle = '#000000';
          context.textAlign = 'center';
          context.textBaseline = 'middle';
          context.fillText(text, canvas.width / 2, canvas.height / 2);
          
          const texture = new THREE.CanvasTexture(canvas);
          const spriteMaterial = new THREE.SpriteMaterial({ 
            map: texture,
            transparent: true
          });
          
          const sprite = new THREE.Sprite(spriteMaterial);
          sprite.position.copy(position);
          sprite.scale.set(5, 5, 1);
          
          return sprite;
        };
        
        const label1 = createTextSprite(base, new THREE.Vector3(x1, y1, z1).addScalar(4));
        dnaGroup.add(label1);
        
        const label2 = createTextSprite(complementaryBase, new THREE.Vector3(x2, y2, z2).addScalar(4));
        dnaGroup.add(label2);
      }
    }
    
    // Create backbone strands
    if (backbone1Points.length > 1) {
      const backbone1Curve = new THREE.CatmullRomCurve3(backbone1Points);
      const backbone2Curve = new THREE.CatmullRomCurve3(backbone2Points);
      
      const backboneTubeGeometry1 = new THREE.TubeGeometry(
        backbone1Curve, 
        nucleotides.length * 2, // tubular segments
        1.5, // radius
        8, // radial segments
        false // closed
      );
      
      const backboneTubeGeometry2 = new THREE.TubeGeometry(
        backbone2Curve, 
        nucleotides.length * 2, // tubular segments
        1.5, // radius
        8, // radial segments
        false // closed
      );
      
      const backboneMaterial = new THREE.MeshPhongMaterial({ 
        color: colors.backbone,
        shininess: 30,
        transparent: true,
        opacity: 0.8
      });
      
      const backboneTube1 = new THREE.Mesh(backboneTubeGeometry1, backboneMaterial);
      backboneTube1.userData = { 
        type: 'backbone',
        info: componentInfo.backbone
      };
      dnaGroup.add(backboneTube1);
      
      const backboneTube2 = new THREE.Mesh(backboneTubeGeometry2, backboneMaterial);
      backboneTube2.userData = { 
        type: 'backbone',
        info: componentInfo.backbone
      };
      dnaGroup.add(backboneTube2);
    }
    
    // Add the DNA group to the scene
    sceneRef.current.add(dnaGroup);
    
    // Add raycasting for interactive selection
    setupRaycasting();
  };
  
  // Setup raycasting for interactive component selection
  const setupRaycasting = () => {
    if (!mountRef.current || !rendererRef.current) return;
    
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    
    const onMouseClick = (event) => {
      // Calculate mouse position in normalized device coordinates
      const rect = rendererRef.current.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      
      // Update the picking ray with the camera and mouse position
      raycaster.setFromCamera(mouse, cameraRef.current);
      
      // Calculate objects intersecting the picking ray
      if (objectsRef.current.dnaGroup) {
        const intersects = raycaster.intersectObjects(objectsRef.current.dnaGroup.children, true);
        
        if (intersects.length > 0) {
          const object = intersects[0].object;
          if (object.userData && object.userData.type) {
            setSelectedComponent({
              type: object.userData.type,
              base: object.userData.base || null,
              info: object.userData.info || "No information available"
            });
          }
        }
      }
    };
    
    rendererRef.current.domElement.addEventListener('click', onMouseClick);
    
    // Cleanup function
    return () => {
      if (rendererRef.current && rendererRef.current.domElement) {
        rendererRef.current.domElement.removeEventListener('click', onMouseClick);
      }
    };
  };

  const handleInputChange = (e) => {
    // Filter input to only allow A, T, C, G
    const filtered = e.target.value.toUpperCase().replace(/[^ATCG]/g, '');
    setNucleotides(filtered);
  };

  const handleComponentClick = (component) => {
    setSelectedComponent({
      type: component,
      info: componentInfo[component] || `${component}: No information available.`
    });
  };
  
  const toggleViewMode = () => {
    setViewMode(prev => prev === '3d' ? '2d' : '3d');
  };
  
  const generateRandomSequence = () => {
    const bases = ['A', 'T', 'C', 'G'];
    let sequence = '';
    const length = Math.floor(Math.random() * 20) + 10; // 10-30 bases
    
    for (let i = 0; i < length; i++) {
      const randomIndex = Math.floor(Math.random() * 4);
      sequence += bases[randomIndex];
    }
    
    setNucleotides(sequence);
  };
  
  return (
    <div className="flex flex-col items-center p-4 gap-4 bg-gray-100 rounded-lg min-h-screen">
      <h2 className="text-2xl font-bold text-gray-800">3D DNA Visualization Tool</h2>
      
      {/* Controls */}
      <div className="flex flex-wrap gap-4 w-full max-w-3xl mb-4">
        <div className="bg-white p-4 rounded-lg shadow-md flex-1">
          <label className="block mb-2 font-medium">DNA Sequence:</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={nucleotides}
              onChange={handleInputChange}
              className="w-full p-2 border rounded"
              placeholder="Enter DNA sequence (A, T, C, G)"
            />
            <button
              onClick={generateRandomSequence}
              className="px-3 py-2 bg-green-500 text-white rounded hover:bg-green-600"
              title="Generate Random Sequence"
            >
              Random
            </button>
          </div>
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
          <div className="flex gap-2 mt-2">
            <button
              onClick={() => setIsPaused(!isPaused)}
              className="px-4 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 flex-1"
            >
              {isPaused ? 'Resume' : 'Pause'}
            </button>
            <button
              onClick={toggleViewMode}
              className="px-4 py-1 bg-purple-500 text-white rounded hover:bg-purple-600 flex-1"
            >
              {viewMode === '3d' ? '2D View' : '3D View'}
            </button>
          </div>
        </div>
      </div>
      
      <div className="flex gap-4 w-full max-w-3xl">
        <div className="flex-1">
          {/* Visualization Controls */}
          <div className="bg-white p-4 rounded-lg shadow-md mb-4">
            <h3 className="font-medium mb-2">Display Options:</h3>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="showLabels"
                checked={showLabels}
                onChange={() => setShowLabels(!showLabels)}
              />
              <label htmlFor="showLabels">Show Base Labels</label>
            </div>
          </div>
          
          {/* Legend */}
          <div className="bg-white p-4 rounded-lg shadow-md">
            <h3 className="font-medium mb-2">Color Legend:</h3>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(colors).map(([component, color]) => (
                <div key={component} className="flex items-center cursor-pointer" onClick={() => handleComponentClick(component)}>
                  <div 
                    style={{ backgroundColor: `#${color.toString(16).padStart(6, '0')}` }} 
                    className="w-4 h-4 mr-1 rounded"
                  ></div>
                  <span className="capitalize">{component}</span>
                </div>
              ))}
            </div>
            <p className="text-sm text-gray-600 mt-2">Click on any component to learn more</p>
          </div>
        </div>
        
        {/* Information Panel */}
        <div className="bg-white p-4 rounded-lg shadow-md flex-1">
          <h3 className="font-medium mb-2">Component Information:</h3>
          {selectedComponent ? (
            <div>
              <h4 className="font-semibold">{selectedComponent.base || selectedComponent.type}</h4>
              <p>{selectedComponent.info}</p>
            </div>
          ) : (
            <p>Click on a component in the visualization or legend to see information.</p>
          )}
          
          {/* Instructions */}
          <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm">
            <h4 className="font-semibold text-blue-800">Interaction Tips:</h4>
            <ul className="list-disc pl-5 text-blue-700">
              <li>Drag to rotate the view</li>
              <li>Scroll to zoom in/out</li>
              <li>Click on any component to see information</li>
              <li>Use the controls to adjust speed and view</li>
            </ul>
          </div>
        </div>
      </div>
      
      {/* 3D Visualization Container */}
      <div 
        ref={mountRef} 
        className="bg-white p-4 rounded-lg shadow-md w-full max-w-3xl"
        style={{ height: '500px' }}
      />
      
      {/* Educational Section */}
      <div className="bg-white p-4 rounded-lg shadow-md w-full max-w-3xl mt-4">
        <h3 className="font-medium mb-2">About DNA Structure:</h3>
        <p className="mb-2">
          DNA (deoxyribonucleic acid) forms a double helix structure made up of two complementary strands. 
          Each strand consists of a sugar-phosphate backbone with attached nitrogenous bases.
        </p>
        <p>
          The four bases in DNA are Adenine (A), Thymine (T), Cytosine (C), and Guanine (G). 
          These bases pair specifically: A with T and C with G, held together by hydrogen bonds.
        </p>
      </div>
    </div>
  );
}