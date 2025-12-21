/**
 * Avatar3D Component
 * Realistic 3D avatar with video call quality
 */
import { useRef, useEffect, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { useGLTF } from '@react-three/drei';
import * as THREE from 'three';
import './Avatar3D.css';

interface Avatar3DProps {
  gender: 'male' | 'female';
  isSpeaking: boolean;
  emotion?: 'neutral' | 'happy' | 'sad' | 'surprised';
}

function RealisticAvatar({ gender, isSpeaking }: Avatar3DProps) {
  const groupRef = useRef<THREE.Group>(null);
  const [, setMorphTargetInfluences] = useState<number[]>([]);
  
  // Ready Player Me avatar URLs (free realistic avatars)
  const avatarUrl = gender === 'female' 
    ? 'https://models.readyplayer.me/64bfa15f0e72c63d7c3934a6.glb' // Female avatar
    : 'https://models.readyplayer.me/64bfa15f0e72c63d7c3934a7.glb'; // Male avatar

  // Load 3D model
  const gltf = useGLTF(avatarUrl);
  
  useEffect(() => {
    if (gltf && gltf.scene) {
      // Find mesh with morph targets for facial animation
      gltf.scene.traverse((child: any) => {
        if ((child as THREE.Mesh).isMesh) {
          const mesh = child as THREE.Mesh;
          if (mesh.morphTargetInfluences) {
            setMorphTargetInfluences(mesh.morphTargetInfluences);
          }
        }
      });
    }
  }, [gltf]);

  // Animate avatar
  useFrame((state) => {
    if (groupRef.current) {
      const time = state.clock.getElapsedTime();
      
      if (isSpeaking) {
        // Lip sync animation
        const lipValue = Math.abs(Math.sin(time * 15)) * 0.6;
        
        // Animate mouth morph targets if available
        gltf.scene.traverse((child: any) => {
          if ((child as THREE.Mesh).isMesh) {
            const mesh = child as THREE.Mesh;
            if (mesh.morphTargetInfluences && mesh.morphTargetDictionary) {
              // Animate mouth open
              if (mesh.morphTargetDictionary['mouthOpen']) {
                const index = mesh.morphTargetDictionary['mouthOpen'];
                mesh.morphTargetInfluences[index] = lipValue;
              }
            }
          }
        });
        
        // Natural head movement while speaking
        groupRef.current.rotation.y = Math.sin(time * 0.5) * 0.15;
        groupRef.current.rotation.x = Math.sin(time * 0.3) * 0.08;
        groupRef.current.position.y = Math.sin(time * 2) * 0.02;
      } else {
        // Idle breathing animation
        groupRef.current.position.y = Math.sin(time * 1.5) * 0.01;
        groupRef.current.rotation.y = Math.sin(time * 0.2) * 0.05;
        
        // Close mouth
        gltf.scene.traverse((child: any) => {
          if ((child as THREE.Mesh).isMesh) {
            const mesh = child as THREE.Mesh;
            if (mesh.morphTargetInfluences && mesh.morphTargetDictionary) {
              if (mesh.morphTargetDictionary['mouthOpen']) {
                const index = mesh.morphTargetDictionary['mouthOpen'];
                mesh.morphTargetInfluences[index] *= 0.9;
              }
            }
          }
        });
      }
    }
  });

  return (
    <group ref={groupRef}>
      <primitive object={gltf.scene} scale={2} position={[0, -1.5, 0]} />
    </group>
  );
}

// Fallback simple avatar if model fails to load
function FallbackAvatar({ gender, isSpeaking }: Avatar3DProps) {
  const groupRef = useRef<THREE.Group>(null);
  const [mouthScale, setMouthScale] = useState(1);

  useFrame((state) => {
    if (groupRef.current) {
      const time = state.clock.getElapsedTime();
      
      if (isSpeaking) {
        const newScale = Math.abs(Math.sin(time * 15)) * 0.5 + 0.5;
        setMouthScale(newScale);
        groupRef.current.rotation.y = Math.sin(time * 0.5) * 0.1;
      } else {
        setMouthScale(1);
        groupRef.current.rotation.y *= 0.95;
      }
    }
  });

  const skinColor = gender === 'female' ? '#ffd4a3' : '#e8b896';
  const hairColor = gender === 'female' ? '#4a2c2a' : '#2c1810';
  const clothingColor = gender === 'female' ? '#e91e63' : '#2196f3';

  return (
    <group ref={groupRef}>
      {/* Head */}
      <mesh position={[0, 0.5, 0]}>
        <sphereGeometry args={[0.5, 32, 32]} />
        <meshStandardMaterial color={skinColor} />
      </mesh>

      {/* Eyes */}
      <mesh position={[-0.15, 0.6, 0.4]}>
        <sphereGeometry args={[0.05, 16, 16]} />
        <meshStandardMaterial color="#ffffff" />
      </mesh>
      <mesh position={[0.15, 0.6, 0.4]}>
        <sphereGeometry args={[0.05, 16, 16]} />
        <meshStandardMaterial color="#ffffff" />
      </mesh>
      <mesh position={[-0.15, 0.6, 0.45]}>
        <sphereGeometry args={[0.025, 16, 16]} />
        <meshStandardMaterial color="#1a1a1a" />
      </mesh>
      <mesh position={[0.15, 0.6, 0.45]}>
        <sphereGeometry args={[0.025, 16, 16]} />
        <meshStandardMaterial color="#1a1a1a" />
      </mesh>

      {/* Mouth */}
      <mesh position={[0, 0.35, 0.4]} scale={[1, mouthScale, 1]}>
        <capsuleGeometry args={[0.05, 0.15, 8, 16]} rotation={[0, 0, Math.PI / 2]} />
        <meshStandardMaterial color="#d4756e" />
      </mesh>

      {/* Hair */}
      <mesh position={[0, 0.75, 0]}>
        <sphereGeometry args={[0.52, 32, 32, 0, Math.PI * 2, 0, Math.PI * 0.6]} />
        <meshStandardMaterial color={hairColor} />
      </mesh>

      {/* Body */}
      <mesh position={[0, -0.3, 0]}>
        <cylinderGeometry args={[0.25, 0.35, 0.8, 32]} />
        <meshStandardMaterial color={clothingColor} />
      </mesh>
    </group>
  );
}

export function Avatar3D({ gender, isSpeaking, emotion }: Avatar3DProps) {
  const [useRealistic] = useState(true);
  const [loadError] = useState(false);

  return (
    <div className="avatar-3d-container">
      <Canvas 
        camera={{ position: [0, 0, 3], fov: 50 }}
        onCreated={({ gl }) => {
          gl.setClearColor('#667eea');
        }}
      >
        <ambientLight intensity={0.6} />
        <directionalLight position={[5, 5, 5]} intensity={0.8} castShadow />
        <pointLight position={[-5, 3, -5]} intensity={0.4} />
        <spotLight position={[0, 5, 0]} intensity={0.5} angle={0.3} penumbra={1} />
        
        {!loadError && useRealistic ? (
          <RealisticAvatar 
            gender={gender} 
            isSpeaking={isSpeaking} 
            emotion={emotion}
          />
        ) : (
          <FallbackAvatar 
            gender={gender} 
            isSpeaking={isSpeaking} 
            emotion={emotion}
          />
        )}
      </Canvas>
      
      <div className="avatar-status">
        {isSpeaking && (
          <div className="speaking-indicator">
            <span className="pulse-dot"></span>
            <span>Speaking...</span>
          </div>
        )}
      </div>
    </div>
  );
}
