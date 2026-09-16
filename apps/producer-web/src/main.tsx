import { useState } from "react";
import { createRoot } from "react-dom/client";
import axios from "axios";
import { Button, ConfigProvider, Form, Steps, Tag, Typography } from "antd";
import ptBR from "antd/locale/pt_BR";
import {
  Aside,
  Brand,
  Columns,
  Eyebrow,
  FieldHelp,
  Footer,
  GlobalStyle,
  Header,
  Intro,
  Main,
  MessageInput,
  Notice,
  Panel,
  SectionHeading,
  theme,
} from "./styles";

type Message = { id: string; text: string; createdAt: string };
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/producer",
  timeout: 12000,
});
const consumerUrl = import.meta.env.DEV
  ? "http://localhost:5174/consumer/"
  : "/consumer/";

function App() {
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState<Message | null>(null);
  const length = Array.from(text.trim()).length;
  const valid = length > 0 && length <= 1000 && !text.includes("\0");

  async function publish() {
    if (!valid || sending) return;
    setSending(true);
    setError("");
    setMessage(null);
    try {
      const response = await api.post<Message>("/messages", {
        text: text.trim(),
      });
      setMessage(response.data);
      setText("");
    } catch (cause) {
      const detail = axios.isAxiosError(cause)
        ? cause.response?.data?.error
        : null;
      setError(
        typeof detail === "string"
          ? detail
          : "Não foi possível confirmar o envio. Confira o histórico antes de tentar novamente.",
      );
    } finally {
      setSending(false);
    }
  }

  return (
    <>
      <GlobalStyle />
      <Header>
        <Brand href="/producer/">
          <span aria-hidden="true">m.</span> mensageria
        </Brand>
        <nav aria-label="Navegação principal">
          <a href="/producer/" aria-current="page">
            Publicar
          </a>
          <a href={consumerUrl}>
            Histórico <span aria-hidden="true">↗</span>
          </a>
        </nav>
      </Header>
      <Main>
        <Intro>
          <Eyebrow>01 / PRODUTOR</Eyebrow>
          <h1>
            Uma mensagem.
            <br />
            <span>O início de uma conversa.</span>
          </h1>
          <p>
            Escreva, publique e acompanhe a chegada da sua mensagem no
            histórico.
          </p>
        </Intro>
        <Columns>
          <Panel>
            <SectionHeading>
              <h2>Nova mensagem</h2>
              <Tag>Texto livre</Tag>
            </SectionHeading>
            <Form layout="vertical" onFinish={publish}>
              <Form.Item label="O que você quer enviar?" htmlFor="message">
                <MessageInput
                  id="message"
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                  disabled={sending}
                  rows={7}
                  placeholder="Olá! Esta é a minha primeira mensagem."
                  aria-describedby="message-help"
                  aria-invalid={length > 1000}
                  status={length > 1000 ? "error" : undefined}
                />
              </Form.Item>
              <FieldHelp id="message-help">
                <span>De 1 a 1.000 caracteres.</span>
                <Typography.Text type={length > 1000 ? "danger" : "secondary"}>
                  {length.toLocaleString("pt-BR")} / 1.000
                </Typography.Text>
              </FieldHelp>
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                block
                loading={sending}
                disabled={!valid || sending}
              >
                {sending ? "Confirmando envio…" : "Publicar mensagem"}{" "}
                <span aria-hidden="true">→</span>
              </Button>
            </Form>
            {error && (
              <Notice type="error" showIcon title={error} role="alert" />
            )}
            {message && (
              <Notice
                type="success"
                showIcon
                role="status"
                title="Publicação confirmada"
                description={
                  <>
                    Sua mensagem foi aceita. Ela aparecerá no histórico após o
                    processamento.
                    <code>{message.id}</code>
                    <Typography.Link href={consumerUrl}>
                      Acompanhar no histórico →
                    </Typography.Link>
                  </>
                }
              />
            )}
          </Panel>
          <Aside>
            <Eyebrow>O CAMINHO DA MENSAGEM</Eyebrow>
            <Steps
              orientation="vertical"
              size="small"
              current={-1}
              items={[
                {
                  title: "Publique",
                  content: "Envie seu texto por este formulário.",
                },
                {
                  title: "Aguarde o processamento",
                  content: "A confirmação de envio é o primeiro passo.",
                },
                {
                  title: "Veja no histórico",
                  content:
                    "Depois de armazenada, sua mensagem fica disponível para consulta.",
                },
              ]}
            />
            <p>
              O histórico é atualizado automaticamente. A mensagem pode levar
              alguns instantes para aparecer.
            </p>
          </Aside>
        </Columns>
      </Main>
      <Footer>
        Laboratório de mensagens <span>Publicar · Processar · Guardar</span>
      </Footer>
    </>
  );
}

createRoot(document.getElementById("root")!).render(
  <ConfigProvider theme={theme} locale={ptBR}>
    <App />
  </ConfigProvider>,
);
