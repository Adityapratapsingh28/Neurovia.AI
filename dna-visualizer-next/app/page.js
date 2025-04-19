import Head from 'next/head';
import DNAVisualizer from '@/components/DNAVisualizer';

export default function Home() {
  return (
    <>
      <Head>
        <title>DNA Visualizer</title>
        <meta name="description" content="Interactive DNA visualization tool" />
      </Head>
      <main className="min-h-screen bg-gray-100 p-4">
        <div className="container mx-auto">
          <header className="mb-8 text-center">
            <h1 className="text-3xl font-bold text-gray-800">DNA Visualization Tool</h1>
            <p className="text-gray-600">Interact with the 3D structure of DNA</p>
          </header>
          <DNAVisualizer />
        </div>
      </main>
    </>
  );
}
