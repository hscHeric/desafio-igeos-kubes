import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import axios from "axios";
import { Button, ConfigProvider, Descriptions, Empty, Spin, Tag } from "antd";
import ptBR from "antd/locale/pt_BR";
import {
  Brand,
  EmptyState,
  Eyebrow,
  Footer,
  GlobalStyle,
  Header,
  Intro,
  Main,
  MessageCard,
  MessageList,
  MessageText,
  Notice,
  Panel,
  SectionHeading,
  Updated,
  theme,
} from "./styles";

type Message = {
  id: string;
  text: string;
  createdAt: string;
  processedAt: string;
};
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/consumer",
  timeout: 8000,
});
const producerUrl = import.meta.env.DEV
  ? "http://localhost:5173/producer/"
  : "/producer/";
const formatDate = (value: string) => new Date(value).toLocaleString("pt-BR");

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updatedAt, setUpdatedAt] = useState("");

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    async function refresh() {
      try {
        const response = await api.get<{ messages: Message[] }>("/messages", {
          signal: controller.signal,
        });
        if (!controller.signal.aborted) {
          setMessages(response.data.messages);
          setUpdatedAt(new Date().toLocaleTimeString("pt-BR"));
          setError("");
        }
      } catch (cause) {
        if (!controller.signal.aborted) {
          const detail = axios.isAxiosError(cause)
            ? cause.response?.data?.error
            : null;
          setError(
            typeof detail === "string"
              ? detail
              : "Não foi possível atualizar o histórico. Tentaremos novamente em instantes.",
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          timer = setTimeout(refresh, 3000);
        }
      }
    }
    void refresh();
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, []);

  return (
    <>
      <GlobalStyle />
      <Header>
        <Brand href={producerUrl}>
          <span aria-hidden="true">m.</span> mensageria
        </Brand>
        <nav aria-label="Navegação principal">
          <a href={producerUrl}>
            Publicar <span aria-hidden="true">↗</span>
          </a>
          <a href="/consumer/" aria-current="page">
            Histórico
          </a>
        </nav>
      </Header>
      <Main>
        <Intro>
          <Eyebrow>02 / CONSUMIDOR</Eyebrow>
          <h1>
            Mensagens que chegaram.
            <br />
            <span>Um histórico que fica.</span>
          </h1>
          <p>
            Acompanhe as últimas 100 mensagens armazenadas, das mais recentes às
            mais antigas.
          </p>
        </Intro>
        <Panel aria-label="Histórico de mensagens">
          <SectionHeading>
            <h2>
              Caixa de entrada <Tag>{messages.length}</Tag>
            </h2>
            <Tag color={error ? "error" : "success"} role="status">
              {loading
                ? "Consultando…"
                : error
                  ? "Atualização indisponível"
                  : "Atualização automática"}
            </Tag>
          </SectionHeading>
          <Updated>
            {updatedAt
              ? `Última consulta bem-sucedida às ${updatedAt}`
              : "Aguardando a primeira consulta."}
          </Updated>
          {error && (
            <Notice
              type="error"
              showIcon
              role="alert"
              title={error}
              description={
                messages.length > 0
                  ? "Exibindo o último histórico recebido."
                  : undefined
              }
            />
          )}
          {loading && (
            <EmptyState role="status">
              <Spin />
              <p>Buscando suas mensagens…</p>
            </EmptyState>
          )}
          {!loading && !error && messages.length === 0 && (
            <EmptyState>
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  <>
                    <h3>A primeira mensagem começa com você.</h3>
                    <p>
                      Publique um texto e volte aqui para acompanhar sua
                      chegada.
                    </p>
                  </>
                }
              >
                <Button type="primary" size="large" href={producerUrl}>
                  Publicar uma mensagem →
                </Button>
              </Empty>
            </EmptyState>
          )}
          <MessageList>
            {messages.map((message) => (
              <li key={message.id}>
                <MessageCard>
                  <MessageText>{message.text}</MessageText>
                  <Descriptions
                    size="small"
                    layout="vertical"
                    column={{ xs: 1, sm: 2 }}
                    items={[
                      {
                        key: "created",
                        label: "Publicada",
                        children: (
                          <time dateTime={message.createdAt}>
                            {formatDate(message.createdAt)}
                          </time>
                        ),
                      },
                      {
                        key: "processed",
                        label: "Armazenada",
                        children: (
                          <time dateTime={message.processedAt}>
                            {formatDate(message.processedAt)}
                          </time>
                        ),
                      },
                    ]}
                  />
                  <code>{message.id}</code>
                </MessageCard>
              </li>
            ))}
          </MessageList>
        </Panel>
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
