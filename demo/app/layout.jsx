import './style.css';

export const metadata = {
  title: 'Slow Burn',
  description: 'A small pilot that measures whether the timestamps shown in a conversation change how often an AI breaks a fictional house rule.',
};

export default function Layout({ children }) {
  return <html lang="en"><body>{children}</body></html>;
}
