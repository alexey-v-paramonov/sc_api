import asyncio
import aiohttp
import time
from django.core.management.base import BaseCommand
from django.db.models import Count
from catalog.models import Radio, Stream
from asgiref.sync import sync_to_async


class Command(BaseCommand):
    help = 'Check all radio streams and update enabled status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of stream URLs to check concurrently (default: 10)'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=5,
            help='Timeout in seconds for each stream check (default: 5)'
        )

    async def check_stream_url(self, stream, timeout):
        """
        Asynchronously check if a stream URL is valid and returns audio content
        Based on StreamSerializer.validate_stream_url
        """
        url = stream.stream_url
        
        if not (url.startswith('http://') or url.startswith('https://')):
            self.stdout.write(self.style.WARNING(f"Invalid URL format: {url}"))
            return False

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Icy-MetaData': '1'  # Request metadata from Shoutcast/Icecast servers
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=timeout) as response:
                    if not response.ok:
                        self.stdout.write(self.style.WARNING(f"HTTP error {response.status}: {url}"))
                        return False
                    
                    # Check if Content-Type header indicates an audio stream
                    content_type = response.headers.get('Content-Type', '').lower()
                    if 'audio' not in content_type:
                        self.stdout.write(self.style.WARNING(f"Not audio content: {url} (Content-Type: {content_type})"))
                        return False
                    
                    self.stdout.write(self.style.SUCCESS(f"Valid audio stream: {url}"))
                    return True
                    
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            self.stdout.write(self.style.WARNING(f"Connection error: {url} ({str(e)})"))
            return False

    async def process_batch(self, streams_batch, timeout):
        """Process a batch of streams concurrently"""
        tasks = [self.check_stream_url(stream, timeout) for stream in streams_batch]
        results = await asyncio.gather(*tasks)
        return dict(zip([stream.id for stream in streams_batch], results))

    @sync_to_async
    def get_all_radios_with_streams(self):
        """Get all radios with their streams"""
        return list(Radio.objects.all().prefetch_related('streams'))

    @sync_to_async
    def update_radio_status(self, radio_id, enabled):
        """Update radio enabled status"""
        Radio.objects.filter(id=radio_id).update(enabled=enabled)

    async def handle_async(self, batch_size, timeout):
        start_time = time.time()
        radios = await self.get_all_radios_with_streams()
        total_radios = len(radios)
        
        self.stdout.write(self.style.SUCCESS(f"Checking {total_radios} radios..."))
        
        # Process each radio
        radios_updated = 0
        
        for radio in radios:
            streams = list(radio.streams.all())
            
            if not streams:
                self.stdout.write(self.style.WARNING(f"Radio '{radio.name}' has no streams. Setting enabled=False"))
                await self.update_radio_status(radio.id, False)
                radios_updated += 1
                continue
                
            # Process streams in batches
            stream_results = {}
            for i in range(0, len(streams), batch_size):
                batch = streams[i:i + batch_size]
                batch_results = await self.process_batch(batch, timeout)
                stream_results.update(batch_results)
            
            # Check if any stream is valid
            has_valid_stream = any(stream_results.values())
            
            # Update radio status if necessary
            if has_valid_stream != radio.enabled:
                await self.update_radio_status(radio.id, has_valid_stream)
                status_text = "enabled" if has_valid_stream else "disabled"
                self.stdout.write(
                    self.style.SUCCESS(f"Updated radio '{radio.name}' status: {status_text}")
                )
                radios_updated += 1
        
        duration = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f"Completed in {duration:.2f} seconds. "
                f"Updated {radios_updated} out of {total_radios} radios."
            )
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        timeout = options['timeout']
        
        self.stdout.write(self.style.SUCCESS(f"Starting stream check with batch size: {batch_size}"))
        
        # Run the async handler
        asyncio.run(self.handle_async(batch_size, timeout))