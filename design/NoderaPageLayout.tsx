import React from 'react';
import { Button } from '@/components/ui/button';
import { NODERA_DESIGN_SYSTEM as DS, HERO_SHAPES } from '@/design-system/nodera-bauhaus';

interface NoderaPageLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  welcomeText?: string;
  primaryButton?: {
    text: string;
    onClick: () => void;
    color?: 'red' | 'blue';
  };
  secondaryButton?: {
    text: string;
    onClick: () => void;
  };
  heroShapes?: keyof typeof HERO_SHAPES;
  showHero?: boolean;
}

export function NoderaPageLayout({
  children,
  title,
  subtitle,
  welcomeText,
  primaryButton,
  secondaryButton,
  heroShapes = 'default',
  showHero = true
}: NoderaPageLayoutProps) {
  // Get the shape configuration
  const shapes = HERO_SHAPES[heroShapes];
  
  return (
    <div className="bauhaus-theme">
      {showHero && (
        <section className={`relative ${DS.spacing.hero} overflow-hidden bg-white`}>
          {/* Geometric Bauhaus shapes */}
          {shapes.left && (
            <div className={`absolute left-0 top-0 ${DS.shapes[shapes.left.size as keyof typeof DS.shapes]}`}>
              <div className={`absolute inset-0 ${shapes.left.type === 'circle' ? 'rounded-full' : 'rotate-45'}`} 
                   style={{backgroundColor: DS.colors[shapes.left.color as keyof typeof DS.colors]}}></div>
            </div>
          )}
          
          {shapes.right && (
            <div className={`absolute right-10 top-20 ${DS.shapes[shapes.right.size as keyof typeof DS.shapes]}`}>
              <div className={`absolute inset-0 ${shapes.right.type === 'circle' ? 'rounded-full' : 'rotate-45'}`} 
                   style={{backgroundColor: DS.colors[shapes.right.color as keyof typeof DS.colors]}}></div>
            </div>
          )}
          
          {shapes.bottom && (
            <div className={`absolute left-1/4 bottom-0 ${DS.shapes[shapes.bottom.size as keyof typeof DS.shapes]}`}>
              <div className={`absolute inset-0 ${shapes.bottom.type === 'circle' ? 'rounded-full' : 'rotate-45'}`} 
                   style={{backgroundColor: DS.colors[shapes.bottom.color as keyof typeof DS.colors]}}></div>
            </div>
          )}
          
          <div className={`${DS.layout.container} relative text-center px-6 z-10`}>
            {welcomeText && (
              <div className="inline-block bg-white px-6 py-2 shadow-lg mb-6">
                <h2 className={`${DS.typography.h2}`} style={{color: DS.colors.blue}}>
                  {welcomeText}
                </h2>
              </div>
            )}
            
            <h1 className={`${DS.typography.hero} mb-6 inline-block px-4 py-2 bg-white border-8 border-black`}>
              {title}
            </h1>
            
            {subtitle && (
              <p className={`${DS.typography.body} max-w-2xl mx-auto mb-8`}>
                {subtitle}
              </p>
            )}
            
            {(primaryButton || secondaryButton) && (
              <div className="flex flex-wrap justify-center gap-4">
                {primaryButton && (
                  <Button 
                    size="lg" 
                    className="px-8 py-3 text-lg rounded-none shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] gap-2"
                    style={{
                      backgroundColor: DS.colors[primaryButton.color || 'red'], 
                      color: DS.colors.white
                    }}
                    onClick={primaryButton.onClick}
                  >
                    {primaryButton.text}
                  </Button>
                )}
                
                {secondaryButton && (
                  <Button 
                    size="lg" 
                    className="px-8 py-3 text-lg rounded-none"
                    style={{
                      backgroundColor: DS.colors.white, 
                      color: DS.colors.black, 
                      border: `4px solid ${DS.colors.black}`
                    }}
                    onClick={secondaryButton.onClick}
                  >
                    {secondaryButton.text}
                  </Button>
                )}
              </div>
            )}
          </div>
        </section>
      )}
      
      {/* Content Sections */}
      <div className={`${DS.layout.container} px-6 ${DS.spacing.content} ${DS.spacing.between}`}>
        {children}
      </div>
    </div>
  );
}
