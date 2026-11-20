import HeroSection from '../components/HeroSection';
import FeaturedModels from '../components/FeaturedModels';
import ComparisonPreview from '../components/ComparisonPreview';
import Footer from '../components/Footer';

export default function HomePage({ setCurrentPage }) {
  return (
    <div>
      <HeroSection setCurrentPage={setCurrentPage} />
      <FeaturedModels setCurrentPage={setCurrentPage} />
      <ComparisonPreview />
      <Footer />
    </div>
  );
}
