package com.panda.order_producer.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.panda.order_producer.model.OrderCreated;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.stereotype.Service;

import java.util.concurrent.CompletableFuture;

@Service
@Slf4j
@RequiredArgsConstructor
public class OrderProducer {
    private static final String TOPIC = "order-created";

    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;

    /**
     * Sends an OrderCreated event to Kafka.
     *
     * @param order the order event to send
     * @throws JsonProcessingException if serialization fails
     */
    public void sendOrderCreatedEvent(OrderCreated order) throws JsonProcessingException {
        String correlationId = order.getCorrelationId();
        String orderId       = order.getOrderId();
        String orderJson     = objectMapper.writeValueAsString(order);

        long startTime = System.currentTimeMillis();

        log.debug("Preparing to send event - correlationId: {}, orderId: {}, size: {} bytes",
                correlationId, orderId, orderJson.length());

        CompletableFuture<SendResult<String, String>> future = kafkaTemplate.send(TOPIC, orderId, orderJson);

        future.whenComplete((result, ex) -> {
            long duration = System.currentTimeMillis() - startTime;

            if (ex == null) {
                log.info("Event sent to Kafka - correlationId: {}, orderId: {}, partition: {}, offset: {}, durationMs: {}",
                        correlationId,
                        orderId,
                        result.getRecordMetadata().partition(),
                        result.getRecordMetadata().offset(),
                        duration
                );
            }
            else {
                log.error("Failed to send event - correlationId: {}, orderId: {}, durationMs: {}, error: {}",
                        correlationId, orderId, duration, ex.getMessage());
            }
        });
    }
}
