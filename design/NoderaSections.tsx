import React from 'react';
import { NODERA_DESIGN_SYSTEM as DS } from '@/design-system/nodera-bauhaus';

// Main content section with left border accent
export function NoderaSection({ 
  children, 
  title, 
  subtitle,
  borderColor = 'red',
  leftAccent = true,
  className = ""
}: {
  children: React.ReactNode;
  title: string;
  subtitle?: string;
  borderColor?: keyof typeof DS.colors;
  leftAccent?: boolean;
  className?: string;
}) {
  return (
    <div className={`relative ${className}`}>
      {leftAccent && (
        <div className={`absolute -left-8 top-0 ${DS.shapes.accent} rounded-full -z-10`}
             style={{backgroundColor: DS.colors[borderColor]}}></div>
      )}
      
      <div className={`border-l-8 pl-8`}
           style={{borderColor: DS.colors[borderColor]}}>
        <div className="space-y-8">
          <div>
            <h2 className={`${DS.typography.h2} mb-4`}>{title}</h2>
            {subtitle && <p className={`${DS.typography.body}`}>{subtitle}</p>}
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}

// Feature grid for displaying feature lists
export function NoderaFeatureGrid({ features }: {
  features: Array<{
    icon: React.ReactNode;
    title: string;
    description: string;
    color: keyof typeof DS.colors;
  }>;
}) {
  return (
    <div className="space-y-6 mt-4">
      {features.map((feature, index) => (
        <div key={index} className="flex">
          <div className={`flex-shrink-0 flex items-center justify-center w-12 h-12 mr-4`}
               style={{backgroundColor: DS.colors[feature.color]}}>
            {feature.icon}
          </div>
          <div>
            <h3 className={`${DS.typography.h3}`}>{feature.title}</h3>
            <p>{feature.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// Info box for highlighted content
export function NoderaInfoBox({ 
  children, 
  className = "",
  borderColor = 'black',
  backgroundColor = 'white',
  title,
  subtitle
}: {
  children: React.ReactNode;
  className?: string;
  borderColor?: keyof typeof DS.colors;
  backgroundColor?: keyof typeof DS.colors;
  title?: string;
  subtitle?: string;
}) {
  return (
    <div className={`border-4 border-black p-12 relative ${className}`}
         style={{
           borderColor: DS.colors[borderColor],
           backgroundColor: DS.colors[backgroundColor],
           color: backgroundColor === 'white' ? DS.colors.black : DS.colors.white
         }}>
      {title && (
        <div className="text-center mb-8">
          <h2 className={`${DS.typography.h2} mb-3`} style={{color: backgroundColor === 'white' ? DS.colors.black : DS.colors.white}}>{title}</h2>
          {subtitle && <p className={`${DS.typography.body}`} style={{color: backgroundColor === 'white' ? DS.colors.black : DS.colors.white}}>{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  );
}

// Grid section for flexible layouts
export function NoderaGrid({ 
  children, 
  cols = 2, 
  className = "",
  gap = "gap-8"
}: {
  children: React.ReactNode;
  cols?: 1 | 2 | 3 | 4;
  className?: string;
  gap?: string;
}) {
  const gridCols = cols === 1 ? 'grid-cols-1' : 
                   cols === 2 ? 'md:grid-cols-2' : 
                   cols === 3 ? 'md:grid-cols-3' : 
                   'md:grid-cols-4';
  
  return (
    <div className={`grid ${gridCols} ${gap} ${className}`}>
      {children}
    </div>
  );
}

// Card section for individual content blocks
export function NoderaCard({ 
  children, 
  className = "",
  borderColor = 'black',
  backgroundColor = 'white',
  padding = "p-4"
}: {
  children: React.ReactNode;
  className?: string;
  borderColor?: keyof typeof DS.colors;
  backgroundColor?: keyof typeof DS.colors;
  padding?: string;
}) {
  return (
    <div className={`border-2 border-black ${padding} ${className}`}
         style={{
           borderColor: DS.colors[borderColor],
           backgroundColor: DS.colors[backgroundColor],
           color: backgroundColor === 'white' ? DS.colors.black : DS.colors.white
         }}>
      {children}
    </div>
  );
}

// Centered content section
export function NoderaCenteredSection({ 
  children, 
  title,
  subtitle,
  className = ""
}: {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
}) {
  return (
    <div className={`text-center ${className}`}>
      {title && <h2 className={`${DS.typography.h2} mb-4`}>{title}</h2>}
      {subtitle && <p className={`${DS.typography.body} mb-8`}>{subtitle}</p>}
      {children}
    </div>
  );
}

// Feature card for individual features
export function NoderaFeatureCard({ 
  icon, 
  title, 
  description, 
  color = 'blue',
  className = ""
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  color?: keyof typeof DS.colors;
  className?: string;
}) {
  return (
    <div className={`text-center ${className}`}>
      <div className={`w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center`}
           style={{backgroundColor: DS.colors[color]}}>
        {icon}
      </div>
      <h3 className={`${DS.typography.h3} mb-2`}>{title}</h3>
      <p>{description}</p>
    </div>
  );
}
