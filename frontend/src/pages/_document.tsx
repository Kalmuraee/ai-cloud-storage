import { Html, Head, Main, NextScript } from 'next/document'
import { useEffect } from 'react'

export default function Document() {
  return (
    <Html lang="en">
      <Head />
      <body>
        <Main />
        <NextScript />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // Remove Chrome DevTools extension attributes
              const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                  if (mutation.type === 'attributes' && mutation.attributeName?.startsWith('cz-')) {
                    const element = mutation.target;
                    element.removeAttribute(mutation.attributeName);
                  }
                });
              });
              
              observer.observe(document.body, {
                attributes: true,
                attributeFilter: ['cz-shortcut-listen'],
              });
            `,
          }}
        />
      </body>
    </Html>
  )
}
