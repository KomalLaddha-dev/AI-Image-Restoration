import React, { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export default function DustParticles({ count = 300 }) {
  const mesh = useRef();
  
  const dummy = useMemo(() => new THREE.Object3D(), []);
  
  const particles = useMemo(() => {
    const temp = [];
    for (let i = 0; i < count; i++) {
      const t = Math.random() * 100;
      const factor = 20 + Math.random() * 50;
      const speed = 0.005 + Math.random() / 300;
      const xFactor = -30 + Math.random() * 60;
      const yFactor = -30 + Math.random() * 60;
      const zFactor = -30 + Math.random() * 60;
      temp.push({ t, factor, speed, xFactor, yFactor, zFactor, mx: 0, my: 0 });
    }
    return temp;
  }, [count]);

  useFrame((state) => {
    particles.forEach((particle, i) => {
      let { t, factor, speed, xFactor, yFactor, zFactor } = particle;
      
      t = particle.t += speed;
      const a = Math.cos(t) + Math.sin(t) / 10;
      const b = Math.sin(t) + Math.cos(t) / 10;
      const s = Math.cos(t);
      
      // Mouse interaction
      particle.mx += (state.pointer.x * 10 - particle.mx) * 0.02;
      particle.my += (state.pointer.y * 10 - particle.my) * 0.02;
      
      dummy.position.set(
        (particle.mx / 10) + a + xFactor + Math.cos((t / 5) * factor),
        (particle.my / 10) + b + yFactor + Math.sin((t / 5) * factor),
        (particle.my / 10) + b + zFactor + Math.cos((t / 5) * factor)
      );
      
      dummy.scale.setScalar(Math.max(0.01, s * 0.1));
      dummy.updateMatrix();
      
      mesh.current.setMatrixAt(i, dummy.matrix);
    });
    mesh.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={mesh} args={[null, null, count]}>
      <sphereGeometry args={[0.03, 8, 8]} />
      <meshBasicMaterial color="#d4a853" transparent opacity={0.4} />
    </instancedMesh>
  );
}
