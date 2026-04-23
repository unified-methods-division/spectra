FROM oven/bun:1 AS dev

WORKDIR /app

COPY package.json bun.lockb ./
RUN bun install

COPY . .

EXPOSE 5173

ENV CHOKIDAR_USEPOLLING=true
ENV WATCHPACK_POLLING=true

CMD ["bun", "run", "dev", "--host", "0.0.0.0"]