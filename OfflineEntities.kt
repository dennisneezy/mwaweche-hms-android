package com.mwaeche.hms.data

import androidx.room.*

@Entity(tableName = "sync_outbox", indices = [Index(value = ["mutationId"], unique = true)])
data class SyncOutboxEntity(
    @PrimaryKey(autoGenerate = true) val localId: Long = 0,
    val mutationId: String,
    val entityType: String,
    val entityId: String,
    val operation: String,
    val payloadJson: String,
    val baseVersion: Long,
    val createdAtEpochMs: Long,
    val status: String = "PENDING",
    val lastError: String? = null
)

@Entity(tableName = "cached_patient_summary")
data class CachedPatientSummaryEntity(
    @PrimaryKey val patientId: String,
    val displayName: String,
    val updatedAtEpochMs: Long,
    val serverVersion: Long
)

@Dao
interface OfflineDao {
    @Insert(onConflict = OnConflictStrategy.ABORT) suspend fun enqueue(item: SyncOutboxEntity)
    @Query("SELECT * FROM sync_outbox WHERE status = 'PENDING' ORDER BY createdAtEpochMs") suspend fun pending(): List<SyncOutboxEntity>
    @Query("UPDATE sync_outbox SET status = :status, lastError = :error WHERE mutationId = :mutationId") suspend fun setStatus(mutationId: String, status: String, error: String?)
    @Insert(onConflict = OnConflictStrategy.REPLACE) suspend fun cachePatient(item: CachedPatientSummaryEntity)
    @Query("SELECT * FROM cached_patient_summary WHERE patientId = :id") suspend fun patient(id: String): CachedPatientSummaryEntity?
}
