import { HeroSection } from "@/components/home/HeroSection";
import { CategoriesSection } from "@/components/home/CategoriesSection";
import { FeaturedProducts } from "@/components/home/FeaturedProducts";
import { SeasonalSection } from "@/components/home/SeasonalSection";
import { HowItWorks } from "@/components/home/HowItWorks";
import { ProducerMap } from "@/components/home/ProducerMap";
import { Testimonials } from "@/components/home/Testimonials";
import { NewsletterSection } from "@/components/home/NewsletterSection";
import { StatsSection } from "@/components/home/StatsSection";

export default function HomePage() {
  return (
    <>
      <HeroSection />
      <StatsSection />
      <CategoriesSection />
      <FeaturedProducts />
      <SeasonalSection />
      <HowItWorks />
      <ProducerMap />
      <Testimonials />
      <NewsletterSection />
    </>
  );
}
