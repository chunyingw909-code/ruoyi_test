FROM maven:3.9.11-eclipse-temurin-17 AS build

WORKDIR /workspace
COPY system-under-test/ ./
RUN mvn -B -DskipTests package

FROM eclipse-temurin:17-jre-alpine

RUN addgroup -S ruoyi \
    && adduser -S -G ruoyi ruoyi \
    && mkdir -p /app/upload \
    && chown -R ruoyi:ruoyi /app
WORKDIR /app
COPY --from=build /workspace/ruoyi-admin/target/ruoyi-admin.jar /app/app.jar
USER ruoyi
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
