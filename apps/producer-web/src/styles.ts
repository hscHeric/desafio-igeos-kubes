import { Alert, Card, Input, type ThemeConfig } from "antd";
import styled, { createGlobalStyle } from "styled-components";

export const theme: ThemeConfig = {
  token: {
    colorPrimary: "#172c32",
    colorText: "#172c32",
    colorBorder: "#cbd3c9",
    borderRadius: 10,
    fontFamily: 'Inter, system-ui, -apple-system, "Segoe UI", sans-serif',
  },
};

export const GlobalStyle = createGlobalStyle`
  * { box-sizing: border-box; }
  body { margin: 0; color: #172c32; background: #f5f5ef; font-family: Inter, system-ui, -apple-system, "Segoe UI", sans-serif; line-height: 1.5; }
  a { color: inherit; }
  a:focus-visible, button:focus-visible, textarea:focus-visible { outline: 3px solid #b64621; outline-offset: 4px; }
`;
export const Header = styled.header`
  max-width: 1200px;
  padding: 25px 36px;
  margin: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #d9dfd7;
  gap: 20px;
  nav {
    display: flex;
    gap: 8px;
  }
  nav a {
    padding: 8px 15px;
    text-decoration: none;
    font-size: 14px;
    border-radius: 24px;
  }
  nav a[aria-current] {
    background: #e6e9e0;
    font-weight: 650;
  }
  @media (max-width: 700px) {
    padding: 20px;
    gap: 10px;
    nav a {
      padding: 7px 10px;
      font-size: 12px;
    }
  }
`;
export const Brand = styled.a`
  display: flex;
  gap: 10px;
  align-items: center;
  font-weight: 750;
  font-size: 20px;
  letter-spacing: -0.6px;
  text-decoration: none;
  span {
    display: grid;
    place-items: center;
    background: #172c32;
    color: white;
    width: 35px;
    height: 35px;
    border-radius: 10px;
  }
  @media (max-width: 700px) {
    font-size: 17px;
  }
`;
export const Main = styled.main`
  max-width: 1128px;
  padding: 52px 0 70px;
  margin: auto;
  min-height: calc(100vh - 170px);
  @media (max-width: 1200px) {
    margin: 0 36px;
  }
  @media (max-width: 700px) {
    margin: 0 20px;
    padding: 35px 0 45px;
  }
`;
export const Intro = styled.section`
  margin-bottom: 34px;
  max-width: 850px;
  h1 {
    font-size: clamp(32px, 4vw, 49px);
    font-weight: 650;
    line-height: 1.12;
    letter-spacing: -2px;
    margin: 0 0 20px;
  }
  h1 span {
    color: #768274;
  }
  > p:last-child {
    color: #59675e;
    font-size: 16px;
    max-width: 630px;
  }
  @media (max-width: 700px) {
    h1 {
      letter-spacing: -1.2px;
    }
  }
`;
export const Eyebrow = styled.p`
  font-size: 11px;
  font-weight: 750;
  letter-spacing: 2px;
  color: #607166;
  margin: 0 0 16px;
`;
export const Columns = styled.div`
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(240px, 1fr);
  gap: 52px;
  align-items: start;
  @media (max-width: 1200px) {
    gap: 30px;
  }
  @media (max-width: 700px) {
    grid-template-columns: 1fr;
    gap: 8px;
  }
`;
export const Panel = styled(Card)`
  border-color: #d9dfd7;
  border-radius: 16px;
  box-shadow: 0 5px 20px #1d3b3010;
  > .ant-card-body {
    padding: 28px;
  }
  @media (max-width: 700px) {
    > .ant-card-body {
      padding: 20px;
    }
  }
`;
export const SectionHeading = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 24px;
  h2 {
    margin: 0;
    font-size: 19px;
    font-weight: 650;
    letter-spacing: -0.5px;
  }
`;
export const MessageInput = styled(Input.TextArea)`
  && {
    min-height: 180px;
    max-height: 500px;
    background: #fbfcf8;
    padding: 16px;
    font-size: 16px;
    line-height: 1.6;
  }
`;
export const FieldHelp = styled.div`
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: #687366;
  margin: -12px 0 24px;
`;
export const Notice = styled(Alert)`
  margin-top: 20px;
  overflow-wrap: anywhere;
  code {
    display: block;
    font-size: 11px;
    margin: 10px 0;
  }
`;
export const Aside = styled.aside`
  padding: 24px 0;
  > p:last-child {
    font-size: 13px;
    color: #64715f;
    border-top: 1px solid #d9dfd7;
    padding-top: 19px;
    margin-top: 24px;
  }
`;
export const Footer = styled.footer`
  border-top: 1px solid #d9dfd7;
  max-width: 1128px;
  margin: auto;
  padding: 22px 0;
  display: flex;
  justify-content: space-between;
  gap: 20px;
  font-size: 11px;
  color: #687366;
  @media (max-width: 1200px) {
    margin: 0 36px;
  }
  @media (max-width: 700px) {
    margin: 0 20px;
    flex-direction: column;
    gap: 5px;
  }
`;
